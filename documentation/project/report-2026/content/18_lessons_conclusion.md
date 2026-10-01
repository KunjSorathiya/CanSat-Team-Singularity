@@chapter 18 | Lessons and conclusion | What the project would tell the next team — and what the vehicle achieved.@@

## 18.1 Lessons learned

**1. Photograph and identify every part on arrival, and trust registers over silkscreen.** Chip-ID registers settled the barometer's identity (`0x58` for a BMP280, where a BME280 answers `0x60`) and the IMU's (`0x70`), by the only method that settles them. The inspection of every board paid for itself twice: it closed the power-design question (the SD reader is a 3.3 V board) and it fixed the pin map before the first wire was soldered.

**2. The defects that matter most are the ones a test suite cannot reach.** Five thousand host assertions did not find the chip-select ordering, the supply jumper, or the modem's real airtime. All needed a powered board. Write the tests — they caught nine real defects in code that already built — but do not mistake them for evidence about hardware.

**3. A marginal wire is indistinguishable from a broken component.** Two intermittents — a radio that transmitted 5/5 then 0/5, and a card that read perfectly and refused to write — were the same fault on the same kind of wire on two different modules. Shortening the jumper fixed both outright.

**4. Estimates are wrong in both directions, and the scale settles it in a minute.** The avionics estimate was 31 g low, the structure estimate 64 g high. Both had reasoning behind them and both were labelled as estimates. A weighed number replaced each.

**5. Write the operational document early.** Writing the concept of operations found the hover problem: a vehicle that declared a landing while hanging under the drone, twelve seconds before release. No test found it because no test described a hover. Describing the mission minute by minute exposed a state the design had never considered — and the fix, the descent gate, is why the state field was correct for every packet of Flight 1.

**6. Two systems that must agree should have one definition.** The vehicle and the bridge once carried separate copies of the modem parameters; three parsers in three languages disagreed about the packet format. Both were fixed with one shared header and one shared fixture file.

**7. Make the documentation fail the build.** 306 numbers in the documentation are checked against the source that defines them; the checker caught drift repeatedly, including while this report was written.

**8. Write predictions down before the measurement.** The bring-up record lists the prediction beside every measurement; the airtime model survived to within 1.8 %, and the descent model's guarantee — that the 5 m/s cap would hold — held with a factor of two to spare.

**9. Have the analysis ready before the flight.** The four-hour window is short. A tested pipeline turned the organizers' export — duplicated, unordered, four sessions long — into 102 clean packets and a full set of figures without a line of new analysis code.

**10. Re-read the code before repeating a number about it.** The documentation once said the SD log runs at the 30 Hz sensor rate; the row is appended once per telemetry packet. The 30 Hz figure was true of the acquisition loop and quietly became a claim about the log. A stationary bench log of 2,209 rows in 36.8 minutes had shown the real rate all along, to anyone who divided.

## 18.2 Conclusion

The CanSat is a complete system: a flight computer that runs one bounded loop and knows nothing of its hardware, a 433 MHz LoRa link held to the organizers' packet format and receiver limits, sensors whose every number says where it came from, a printed structure with measured safety margin, a canopy sized for the worst case, and a ground station and an analysis pipeline built alongside it. It was verified in three layers — 6,131 automated checks, 94 bench measurements with predictions recorded in advance, and two flights.

**The flights confirmed the design on every quantity they could test.** Both descents were slow (2.27 and 1.88 m/s against a 5 m/s limit), straight, and stable; the release and the canopy opening were visible in every channel at the same instant; Flight 1 was received in full, 41 of 41 packets at 3.09 Hz; the radio link held a margin of at least 14 dB through carry, release and descent; the vehicle came back on the air by itself after its landing, calibrated, armed and transmitted for another 13 seconds; and the structure met its arrival at a load below half of what it had been analysed for.

The software was complete before the hardware existed; the hardware was built in twelve days; and the first descents were the first the vehicle ever made. It behaved the way the model said it would.

<div class="callout result"><div class="ct">The project in one line</div>

A can-sized satellite that senses, decides, transmits and survives — built so that every claim about it can be traced to a measurement.

</div>
