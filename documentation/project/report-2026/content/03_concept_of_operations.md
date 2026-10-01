@@chapter 3 | Concept of operations | The flight as the vehicle lives it: power-on, the command window, arming, launch, deployment, landing — and the logic that detects each.@@

## 3.1 The flight, event by event

@@tab t-conops | Mission milestones and where each number comes from@@

| Milestone | When | Where the number comes from |
|---|---|---|
| Telemetry begins | Immediately at power-on, at 1.43 Hz | No trigger exists in the firmware |
| Command window | 0 – 300 s | `command_window_ms`. The vehicle listens between packets and does not yet arm |
| Window closes | At 300 s, or on an accepted `MAX_RATE` | Whichever is first |
| Max rate | From the close | `auto_max_rate` — **3.09–3.11 Hz measured** |
| **Armed** | 3 s after the close, once re-calibration settles | `arming_delay_ms`; visible as `ST-R11…` |
| `READY → FLIGHT` | 15 m above the pad, held 300 ms (or > 30 m/s² boost) — met while the vehicle is carried up | `launch_altitude_gain_m` |
| Launch altitude | 30.48 m | Rulebook MIS-001 — flown from a terrace at 29.4 / 29.6 m |
| Landing detected | Descent observed, then 3 s at rest | `landing_confirm_ms` |
| Post-impact window | 5.0 s, then `RECOVERY` | `post_impact_transmission_ms` |

**The pad phase is up to five minutes; the flight is under fifteen seconds of it.** That ratio shaped the design: almost everything the vehicle has to get right — calibration, arming, link health — happens while it is sitting still on the ground, where there is time, and almost nothing has to be decided in the air.

## 3.2 The command window and arming

A vehicle that must transmit from power-on has one awkward property: it cannot tell the ground station anything until something is listening, and it cannot be told anything unless it listens. The sealed flight image resolves this with a five-minute **command window**: after power-on the vehicle transmits at 1.43 Hz so that a command can be heard in the gap between packets. When the window closes — or when an authorised `MAX_RATE` command closes it early — the vehicle moves to its fastest transmit pattern by itself, **discards its power-on calibration, re-calibrates where it now sits (on the pad, after the operator has finished with it)**, and arms.

@@fig f-window | d11_command_window.png | The power-on sequence. The watchdog path skips the window: a reset may come mid-flight, and five minutes unarmed and listening would be five minutes without launch or landing detection. | 66%@@

<div class="callout why"><div class="ct">Why a window, and why re-calibrate when it closes</div>

* **Why a window at all.** The rulebook forbids a manual trigger for telemetry, but the team still needs to change the transmit pattern on the pad without re-flashing. A listening window that closes by itself keeps both rules: nothing is required of an operator, and an operator can still intervene.
* **Why 1.43 Hz inside it.** Listening needs gaps between packets. At 700 ms a 324 ms packet leaves 376 ms of receive time per cycle, and the rate stays above the 1 Hz floor with 43 % margin.
* **Why re-calibrate at the close.** The power-on calibration was taken wherever the vehicle happened to be switched on. The pad is where the baseline must be zero, so the vehicle re-takes it there — gyro bias, accelerometer offset and the barometric ground reference.
* **Why the uplink then closes for good.** Once armed, the vehicle is in every state that holds a log that cannot be recreated. Closing the receiver removes a whole class of ways to disturb it.

</div>

The operator sees arming in the `ST-` status field on every rich packet — `ST-R004` (ready, not armed, 4 faults counted) becomes `ST-R113` (ready, **armed**, **calibrated**) — and in the packet rate rising from 1.43 Hz to about 3.1 Hz. The post-landing session in Chapter 14 shows the sequence exactly: `R004` for the first 5.5 s, then `R113` once calibration settled.

## 3.3 Detecting launch and landing

The state machine has to answer two questions with only a barometer and an accelerometer: *has the vehicle been launched?* and *has it landed?* Both look simple. Neither is.

@@fig f-detect | d06_detection_logic.png | Launch detection (left) and landing detection with the descent gate (right). | 100%@@

### Launch

`READY → FLIGHT` requires the vehicle to be **armed** *and* either a boost above 30 m/s² *or* a climb of more than 15 m above the pad, **held for 300 ms**. Three guards sit in that sentence:

* **Armed** — arming needs the 3 s delay and a settled calibration, so a start-up glitch cannot launch the state machine.
* **Either condition** — a drone lift, or being carried up a building, is a slow climb with almost no acceleration; a throw is a short sharp boost (5.2 g in Flight 1). Both must be recognised, so either may trigger.
* **Held 300 ms** — a knock on the table is shorter than 300 ms; a launch is not.

### Landing, and the problem that the descent gate solves

A vehicle descending under a parachute at a steady rate has no net acceleration: the accelerometer reads about 1 g, exactly as it does sitting on the ground. Landing therefore cannot be an accelerometer test. It is the **vertical rate** that discriminates — a real descent is several metres per second against a 1 m/s threshold.

Writing this concept of operations exposed a subtler problem. A vehicle **hovering under a drone** — or **held still at the edge of a terrace** — also reads 1 g and also has near-zero vertical speed. Run against the real state machine with a 3 m/s climb and a 20 s hover, the original logic produced this:

```text
t= 10362 ms  alt=  16.1 m  rate= +3.0 m/s   READY -> FLIGHT
t= 18018 ms  alt=  30.0 m  rate= +0.0 m/s   FLIGHT -> LANDED     <-- still under the drone
t= 23034 ms  alt=  30.0 m  rate= +0.0 m/s   LANDED -> RECOVERY   <-- 12 s before release
```

The fix is physical rather than tuned: **a vehicle cannot land without descending first.** The state machine latches `descent_observed_` once the vertical rate has been below −2 m/s for one second, and refuses `FLIGHT → LANDED` until it is set. The latch belongs to one `FLIGHT` and clears on any state change; `validate_config()` refuses a descent threshold at or below the at-rest threshold. No hover, however long or gentle, can satisfy it.

<div class="callout why"><div class="ct">Why this matters on 30 September</div>

Flight 1 was held still at the terrace edge, at 29.4 m, for at least 4.3 s before the throw (the first 14 recorded packets) — exactly the condition of a vehicle hovering under a drone: 1 g and no vertical motion. The log shows the vehicle reporting `FLIGHT` throughout the hold and the descent — it never mistook the hold for a landing. The gate is not a theoretical nicety: it is the reason the state field is correct for the whole of Flight 1.

</div>

## 3.4 Launch-day operating sequence

| Step | Operator action | What the vehicle does | What confirms it |
|---|---|---|---|
| 1 | Close the power switch on the ground floor | LED lights at once; telemetry begins; pad calibration | Power LED; packets on the ground station |
| 2 | Wait for the command window to close (or send `MAX_RATE`) | Re-calibrates on the pad, then arms | `ST-R11x`; rate rises to ≈ 3.1 Hz |
| 3 | Hand over to the drone (competition) or carry the vehicle up the building (30 Sep) | Telemetry continues; altitude tracks the lift | Altitude rising in every packet |
| 4 | Drone releases at 100 ft (competition) / thrown from the terrace (30 Sep) | `READY → FLIGHT` (during the lift); canopy deploys | Altitude peak, acceleration spike, descent rate |
| 5 | Vehicle lands | Descent gate opens; 3 s at rest → `LANDED`; 5 s window; `RECOVERY` | Altitude flat at the ground; packets keep arriving |
| 6 | Recover the vehicle; read the card | The SD log holds every packet and the full-precision GPS | `tools/read_flight_log.py` |

**Operating rule: never connect USB while the battery is connected.** USB and the battery are alternative sources for the same Pico supply input, so the vehicle is programmed and bench-tested on USB with the battery disconnected, and flown on the battery alone.

## 3.5 How the 30 September flights were launched

The competition launch is a drone release; for the two flights of 30 September the same 100 ft was obtained from a building terrace, and the vehicle was **thrown by hand like a projectile**, parachute deploying behind it. The procedure was the same as in Section 3.4 with the lift and the release replaced by a staircase and a throw:

| Flight | Power-on | Carried / held | Launch |
|---|---|---|---|
| **1** | At the ground floor, 18:14 IST; command window closed and the vehicle armed at 18:19 | Up the building: the climb past 15 m met the launch condition and the state field read `FLIGHT` for the rest of the record; held still at the terrace edge for at least 4.3 s | Thrown at 18:25:51: a 5.2 g impulse, an upward speed of about 5 m/s, an arc 1.4 m above the hold point, then the canopy |
| **2** | On the terrace, 18:44 IST — so its altitude zero is the terrace and the descent reads −26.9 m | Held on the terrace; still inside the five-minute command window (`ST-R003`, 1.43 Hz) | Thrown at about 18:45:50; the log opens just above the terrace level (+1.0 m), at the top of the throw |

A hand throw is a demanding test of the recovery system: the vehicle leaves the hand moving upward at about 5 m/s with no drone to carry it clear, so the canopy must open from a ballistic start — and it did, within about a second of the apex of the throw.

