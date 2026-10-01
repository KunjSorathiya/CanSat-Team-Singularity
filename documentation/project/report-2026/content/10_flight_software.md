@@chapter 10 | Flight software | The single non-blocking loop, how it reads its sensors, how it decides what state it is in — drawn as flowcharts and quoted from the source.@@

## 10.1 The flight loop

The vehicle runs a **single non-blocking loop on a 2 ms tick.** Nothing waits on hardware, nothing allocates, and every recovery path is bounded.

@@fig f-loop | d03_flight_loop.png | `Controller::poll()` — the whole of the vehicle's behaviour is composed here. | 62%@@

**The ordering is deliberate.** GPS is drained first so a full UART buffer can never back up — at 9600 baud the RP2040's 32-byte FIFO fills in 33 ms, and `validate_config()` enforces that the tick is short enough. Calibration and the state machine run *before* telemetry, so every packet carries the state that matches the samples inside it.

<div class="callout code"><div class="ct">Code · the scheduler (src/scheduler.cpp, complete)</div>

```cpp
bool PeriodicTask::due(std::uint64_t now_ms) {
    if (period_ms_ == 0) return false;
    if (now_ms < next_ms_) return false;
    next_ms_ += period_ms_;
    if (next_ms_ <= now_ms) {          // fell behind by more than one period:
        next_ms_ = now_ms + period_ms_; // re-anchor instead of firing a catch-up burst
    }
    return true;
}
```

`PeriodicTask` is the only timer in the flight core. Its stall rule matters: after a long SD write or a re-initialisation, the loop **does not** transmit a burst of late packets — it re-anchors to `now + period`, keeping the cadence the ground station sees regular.

</div>

## 10.2 Sensor acquisition

@@fig f-acq | d04_sensor_acquisition.png | Sensor acquisition every 33 ms: plausibility gating, staleness and the vertical-rate estimate. | 74%@@

Two rules matter here.

1. **An implausible reading is worse than no reading.** A value outside datasheet-derived bounds (acceleration over 170 m/s², rate over 2200 °/s, pressure outside 30–115 kPa, temperature outside −50…95 °C) is not merely skipped — the previously held value is dropped too, so the vehicle never coasts on data from a sensor that is actively wrong.
2. **Staleness is time-based, not attempt-based.** One failed read changes nothing; two seconds without a good read raises the fault.

### Altitude and vertical rate

The barometric altitude is the standard-atmosphere relation against a ground reference captured at calibration:

<div class="callout code"><div class="ct">Code · sensor_math.cpp</div>

```cpp
double pressure_altitude_m(double pressure_pa, double reference_pressure_pa) {
    if (!(pressure_pa > 0.0) || !(reference_pressure_pa > 0.0)) return 0.0;
    return 44330.0 * (1.0 - std::pow(pressure_pa / reference_pressure_pa, 1.0 / 5.255));
}
```

</div>

The vertical rate is an exponentially weighted average of successive altitude differences (0.7 old + 0.3 new), updated **only when the barometer has produced a new conversion** — re-reading a sensor faster than it converts would otherwise feed repeated values into the derivative and push the estimate toward zero in the middle of a descent. That hold is bounded, because an estimate frozen at a descent rate would stop the landing from ever being detected.

## 10.3 The mission state machine

@@fig f-states | d05_state_machine.png | Every transition and the guard on it. `FAULT` stops state progression, never transmission. | 66%@@

The detection logic itself is short enough to quote. This is the launch test and the descent gate of `state_machine.cpp` (comments abridged):

<div class="callout code"><div class="ct">Code · state_machine.cpp (abridged)</div>

```cpp
case MissionState::ready: {
    if (!in.armed) { launch_condition_since_ms_ = 0; break; }   // ignore motion until armed
    const bool boost = in.accel_magnitude_mps2 > config_.launch_accel_mps2;
    const bool climb = in.altitude_agl_m      > config_.launch_altitude_gain_m;
    if (boost || climb) {
        if (launch_condition_since_ms_ == 0) launch_condition_since_ms_ = now_ms;
        if (now_ms - launch_condition_since_ms_ >= config_.launch_confirm_ms)
            enter(MissionState::flight, now_ms);
    } else launch_condition_since_ms_ = 0;
    break;
}
case MissionState::flight: {
    // The descent gate: a vehicle cannot land without descending first.
    if (in.altitude_rate_mps < -config_.landing_descent_rate_mps) {
        if (descent_since_ms_ == 0) descent_since_ms_ = now_ms;
        if (now_ms - descent_since_ms_ >= config_.landing_descent_confirm_ms)
            descent_observed_ = true;
    } else descent_since_ms_ = 0;

    if (now_ms - entered_ms_ < config_.min_flight_ms) break;
    const double accel_error = std::fabs(in.accel_magnitude_mps2 - sensors::kStandardGravity);
    const bool at_rest = accel_error < config_.landing_accel_epsilon_mps2 &&
                         std::fabs(in.altitude_rate_mps) < config_.landing_altitude_rate_max_mps;
    if (at_rest && descent_observed_) {
        if (rest_condition_since_ms_ == 0) rest_condition_since_ms_ = now_ms;
        if (now_ms - rest_condition_since_ms_ >= config_.landing_confirm_ms)
            enter(MissionState::landed, now_ms);
    } else rest_condition_since_ms_ = 0;
    break;
}
```

</div>

<div class="callout why"><div class="ct">Why each threshold has the value it has</div>

| Constant | Value | Reason |
|---|---:|---|
| `launch_altitude_gain_m` | 15 m | Half the 30 m launch height: far above barometric noise (0.1 m) and anything a hand carries the vehicle through, yet reached with a full 15 m of the climb still ahead — whether the climb is a drone lift or a staircase |
| `launch_accel_mps2` | 30 m/s² | 3 g — above any handling, below any real throw or launch |
| `launch_confirm_ms` | 300 ms | Longer than a knock, shorter than any launch |
| `arming_delay_ms` | 3000 ms | Start-up transients (supply settling, filter convergence) are over |
| `landing_descent_rate_mps` | −2 m/s | Well below the 5 m/s cap, well above hover and noise |
| `landing_accel_epsilon_mps2` | 2.5 m/s² | Within a quarter of 1 g — what “at rest” reads |
| `landing_altitude_rate_max_mps` | 1 m/s | Swing under the canopy sits well below this on the ground |
| `landing_confirm_ms` | 3000 ms | Longer than any bounce, short enough that the 5 s post-impact window starts promptly |
| `post_impact_transmission_ms` | 5000 ms | The rulebook's 5 s; a smaller value will not build |

</div>

## 10.4 Start-up calibration

@@fig f-calib | d07_calibration.png | Pad calibration. Best-effort still produces a usable barometric reference, because averaging pressure does not require stillness. | 66%@@

The asymmetry is intentional. A bias measured while the vehicle was moving would be worse than no correction, so it is discarded — but the **barometric ground reference stays usable** even then. Calibration never blocks the mission. The acceptance test is also two-sided: low variance means "not shaking" but not "not turning" (a constant rotation is perfectly steady), so the mean gyro bias is bounded against the datasheet's zero-rate offset as well.

The post-landing session of Flight 1 shows the calibrator on real data: the transmitted altitude stands at 17.0 m for 5.5 s (the power-on baseline, standard sea level) and then drops to 0.0 ± 0.1 m the instant calibration completes; the yaw channel, which had drifted +0.63 °/s before calibration, is frozen to ±0.1° afterwards.

## 10.5 Telemetry generation and the radio

@@fig f-tx | d08_telemetry_build.png | Building a packet: validity, size shedding and the packet number. | 52%@@

<div class="callout code"><div class="ct">Code · controller.cpp, emit_telemetry (abridged)</div>

```cpp
const std::uint32_t candidate = packet_number_ + 1;
const bool rich = !max_rate_ || max_rate_slot_ == 0;
...
auto built = builder_.build(candidate, mission_ms, snapshot_, extra, rich);
// shed optional content in order of value: status -> sound -> GPS
if (too_long(built)) { extra.clear(); built = builder_.build(candidate, ...); }
if (too_long(built)) { built = builder_.build(candidate, ..., /*air_sound=*/false); }
if (!built) {                         // mandatory data invalid:
    faults_.report(FaultCode::telemetry_suppressed, ...);
    return;                           // no packet, and the number is NOT consumed
}
packet_number_ = candidate;
service_ground_commands(mission_ms);  // BEFORE the transmit: the receive window is the gap
start_with_recovery(built->packet, mission_ms);
if (max_rate_) telemetry_task_.reschedule(mission_ms, rich ? kMaxRateRichSlotMs : kMaxRateLeanSlotMs);
logger_.append(builder_.sd_line(*built, state, faults_.total_occurrences()));
```

</div>

Two details in it carry design decisions. **The command service runs before the transmit** because the receive window is the gap between two packets, and transmitting clears the flags of anything that arrived in it — polling afterwards would read a window that had just been wiped. And **the SD row is written while the packet is still on the air**: the radio sends the packet on its own, so the card write costs no additional time in the cycle.

@@fig f-txrec | d09_radio_recovery.png | Transmit with bounded recovery. A dead radio costs one initialisation per back-off window, never a blocking retry loop. | 56%@@

## 10.6 The fault model

Faults are **classified, not fatal.** Twenty enumerated codes in a fixed-size array — no allocation, constant cost regardless of mission length. A fault carries a severity, an occurrence count and first/last timestamps; severity is monotonic while a fault is active, so a later routine report cannot silently demote one that still applies.

@@tab t-faults | Fault classes and their effect@@

| Class | Effect | Examples |
|---|---|---|
| **Warning** | Counted and reported; nothing else changes | Calibration best-effort, low battery, GPS stale, watchdog restart recorded |
| **Degraded** | A field or a subsystem is dropped; telemetry continues | SD logging disabled after 10 consecutive write failures, radio re-initialising, sound stale |
| **Critical** | `→ FAULT`; state progression stops — **transmission does not** | Invalid configuration, failed self-test, both IMU *and* barometer stale |

The status field makes the fault count visible on the air: `ST-F111` is *flight, armed, calibrated, one fault active*; the watchdog restart after Flight 1's landing is recorded by the same mechanism (`ST-R004` counted four active faults while the vehicle was calibrating, three once it had armed).

## 10.7 Code originality and independence

Every driver in the flight path is **written for this project against its datasheet and register map**: IMU, BMP280, NEO-6M, SX1278 and the SD protocol. There are no third-party libraries anywhere in the flight path.

* The **BMP280 compensation** reproduces the datasheet's own reference vector.
* The **SD driver** implements CMD0/CMD8/ACMD41 initialisation and SDHC versus SDSC block addressing; a **FAT32 reader** walks an MBR, a BPB and a cluster chain to find the log file.
* The **LoRa driver** is register-level and is driven through a callback struct, so the *same* code runs on the vehicle, on the bridge, and against a fake register bank in tests.
* The **GPS parser** is a streaming NMEA-0183 parser (GGA and RMC) with checksum validation and the satellite/HDOP quality gate.
* The **attitude filter** is a Mahony complementary filter on a unit quaternion — chosen over Euler integration because a tumbling CanSat passes through the ±90° pitch singularity that breaks the Euler form. A test drives it through a 20 s tumble at 100 °/s about all three axes.

@@tab t-code-size | The source tree (lines include tests)@@

| Area | Files | Lines | Role |
|---|---:|---:|---|
| `firmware/flight-computer` | 52 | 15,180 | Flight core, Pico hardware layer and their tests |
| `firmware/common` | 9 | 2,244 | Telemetry format and SX1278 driver shared by vehicle and bridge |
| `firmware/ground-station` | 6 | 782 | Bridge firmware and CRC framing |
| `ground-station/software` | 17 | 3,828 | Python receive pipeline and tests |
| `ground-station/web` | 3 | 4,996 | Zero-dependency browser console and tests |
| `simulations` | 2 | 763 | Descent model and tests |
| `tools` | 18 | 5,538 | Link-budget calculator, generators, documentation checker, log utilities |
| `analysis` | 8 | ≈ 3,300 | Post-flight analysis, launch-day analysis and figures |

**18,206 lines of C++ firmware and ≈ 12,800 lines of Python** — all written for this project.

## 10.8 Design rules, restated as behaviour

* **It calibrates itself on the pad — and never lets that block the mission.**
* **A start-up glitch cannot trigger a false launch.** Launch is refused until the vehicle is armed.
* **Wrong data is never transmitted, and suppression never fakes packet loss.**
* **Every peripheral can fail without stopping the mission.** GPS missing → its fields are omitted. SD failing → logging disables itself after ten consecutive failures. Radio down → bounded re-initialisation with a 1 s back-off. Only a total loss of mandatory sensing is critical — and even then telemetry keeps running.
* **It survives its own restarts.** A 2 s hardware watchdog restarts a hung loop; telemetry resumes automatically at the max rate and the restart is reported as a fault so the ground station can see it. Flight 1's post-landing session (Chapter 14) is that path in the log.
