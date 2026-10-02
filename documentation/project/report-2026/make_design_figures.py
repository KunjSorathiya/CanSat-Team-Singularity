#!/usr/bin/env python3
"""Design figures for the final report: block diagrams and flowcharts (Graphviz), and the
engineering charts (matplotlib). Run from anywhere:  python make_design_figures.py

Every number drawn here is either read from the repository (descent model, constants) or
copied from a measurement recorded in documentation/testing/bring-up-record.md.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIG = HERE / "figures"
FIG.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / "simulations"))
sys.path.insert(0, str(ROOT / "analysis" / "flight-2026-09-30"))

import numpy as np  # noqa: E402
import launch_figures as lf  # noqa: E402  (sets the matplotlib style and fonts)
from launch_figures import (F1C, F2C, GOLD, GREEN, INK, MUTED, NAVY, PURPLE, RED, SKY, TEAL,  # noqa: E402
                            _save)
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
import descent  # noqa: E402

# ------------------------------------------------------------------------------------------
# Graphviz helper
# ------------------------------------------------------------------------------------------
HEAD = '''digraph G {
  graph [fontname="Inter", bgcolor="white", pad=0.25, nodesep=0.32, ranksep=0.42, splines=true, %s];
  node  [shape=box, style="rounded,filled", fontname="Inter", fontsize=11, fillcolor="#EFF6FF", color="#1D4ED8",
         fontcolor="#0F172A", penwidth=1.4, margin="0.16,0.09"];
  edge  [fontname="Inter", fontsize=9.5, color="#475569", fontcolor="#475569", arrowsize=0.8, penwidth=1.2];
'''


def dot(name: str, body: str, extra: str = "", dpi: int = 210):
    src = HEAD % extra + body + "\n}\n"
    p = FIG / f"{name}.dot"
    p.write_text(src)
    subprocess.run(["dot", "-Tpng", f"-Gdpi={dpi}", str(p), "-o", str(FIG / f"{name}.png")], check=True)
    p.unlink()
    print("  dot", name)


BLUE = 'fillcolor="#DBEAFE", color="#1D4ED8"'
TEALN = 'fillcolor="#CCFBF1", color="#0F8B8D"'
GOLDN = 'fillcolor="#FEF3C7", color="#D99A00"'
REDN = 'fillcolor="#FEE2E2", color="#D1495B"'
GREENN = 'fillcolor="#DCFCE7", color="#2E9E5B"'
PURP = 'fillcolor="#EDE9FE", color="#7B2CBF"'
GREY = 'fillcolor="#F1F5F9", color="#64748B"'
DIAM = 'shape=diamond, style="filled", fillcolor="#FEF3C7", color="#D99A00", margin="0.05,0.05"'


def diagrams():
    # ---- 1  system architecture -------------------------------------------------------
    dot("d01_architecture", f'''
  rankdir=TB; newrank=true;
  subgraph cluster_v {{ label="VEHICLE  ·  CAN-Team-25"; labeljust=l; fontname="Inter"; fontsize=12; fontcolor="#1D4ED8";
    style="rounded,filled"; fillcolor="#F8FAFF"; color="#93C5FD"; penwidth=1.5;
    bat [label="1S LiPo\\n3.7 V · 1500 mAh", {GOLDN}];
    sw  [label="ON/OFF switch\\n+ power LED", {GOLDN}];
    mcu [label="Raspberry Pi Pico\\nRP2040 · flight computer\\n(controller · state machine ·\\ncalibration · fault manager)", {BLUE}, fontsize=12, penwidth=2.2];
    imu [label="MPU-6500 IMU\\naccel + gyro · I²C 0x68", {TEALN}];
    baro [label="BMP280\\npressure · temperature\\nI²C 0x76", {TEALN}];
    gps [label="NEO-6M GPS\\nUART 9600", {TEALN}];
    mic [label="LM393 microphone\\nADC · GP27", {TEALN}];
    sd [label="microSD\\nraw-block flight log\\nSPI0", {PURP}];
    lora [label="SX1278 RA-02\\n433 MHz LoRa · SPI0", {REDN}];
    ant [label="433 MHz antenna", {GREY}];
    bat -> sw -> mcu [label="3V3 rail"];
    imu -> mcu; baro -> mcu; gps -> mcu; mic -> mcu;
    mcu -> sd [label="every packet"]; mcu -> lora [label="packet"]; lora -> ant;
  }}
  subgraph cluster_g {{ label="GROUND STATION"; labeljust=l; fontname="Inter"; fontsize=12; fontcolor="#0F8B8D";
    style="rounded,filled"; fillcolor="#F4FFFD"; color="#5EEAD4"; penwidth=1.5;
    gant [label="433 MHz antenna", {GREY}];
    glora [label="SX1278 RA-02\\ncontinuous RX", {REDN}];
    bridge [label="Pico bridge\\nCRC-16 framing → USB", {BLUE}];
    pc [label="PC pipeline\\nCRC · parse · validate ·\\nhealth · log", {PURP}];
    ui [label="Web console · Tk dashboard\\nCSV export · replay", {GREENN}];
    gant -> glora -> bridge -> pc -> ui;
  }}
  org [label="Organizers' official\\nground stations\\n(ESP32 + RA-02)", {GOLDN}];
  ant -> gant [style=dashed, label="LoRa SF7 · 125 kHz\\nsync 0xA5", color="#D1495B", fontcolor="#D1495B", penwidth=1.8];
  ant -> org [style=dashed, color="#D99A00", penwidth=1.8];
''', extra='compound=true')

    # ---- 2  layers ---------------------------------------------------------------------
    dot("d02_layers", f'''
  rankdir=TB; node [width=5.6];
  a [label="main.cpp  —  watchdog · clock · configuration", {GREY}];
  b [label="flight::pico  —  hardware: mpu9250 · bmp280 · neo6m · sd_card · pico_radio", {BLUE}];
  c [label="flight::  —  flight core: controller · state machine · scheduler · orientation · calibration ·\\nfault manager · telemetry builder · raw-block log · GPS parser", {BLUE}, penwidth=2.4];
  d [label="cansat::  —  shared: telemetry format & parser · SX1278 driver · link profile", {PURP}];
  e [label="ground::  —  bridge firmware & CRC-16 USB framing", {TEALN}];
  f [label="Python / JavaScript  —  ground pipeline & interfaces", {TEALN}];
  a -> b -> c -> d -> e -> f;
''')

    # ---- 3  flight loop ----------------------------------------------------------------
    dot("d03_flight_loop", f'''
  rankdir=TB;
  s [label="Controller::poll(now_ms)\\ncalled every 2 ms", {BLUE}, penwidth=2.2];
  a [label="capture epoch on first call\\nmission_ms = now − epoch", {GREY}];
  g [label="gps.poll()\\nbounded UART drain · never blocks on a fix", {TEALN}];
  q1 [label="sensor task due?\\n33 ms", {DIAM}];
  s1 [label="acquire_sensors()\\nIMU · barometer · GPS snapshot", {BLUE}];
  c [label="run_calibration()", {BLUE}];
  m [label="feed_state_machine()", {BLUE}];
  q2 [label="telemetry task due?\\n700 ms or 3-slot pattern", {DIAM}];
  t [label="emit_telemetry()\\nbuild → transmit → log", {REDN}];
  q3 [label="SD flush due?\\n2000 ms", {DIAM}];
  f [label="logger.flush()", {PURP}];
  q4 [label="battery / health due?\\n1000 ms", {DIAM}];
  h [label="sample_battery()\\nrefresh_health()", {GREY}];
  l [label="update_led()\\nblink rate encodes mission state", {GOLDN}];
  s -> a -> g -> q1;
  q1 -> s1 [label="yes"]; q1 -> c [label="no"]; s1 -> c -> m -> q2;
  q2 -> t [label="yes"]; q2 -> q3 [label="no"]; t -> q3;
  q3 -> f [label="yes"]; q3 -> q4 [label="no"]; f -> q4;
  q4 -> h [label="yes"]; q4 -> l [label="no"]; h -> l;
  l -> s [label="next tick", style=dashed, constraint=false];
''')

    # ---- 4  sensor acquisition ---------------------------------------------------------
    dot("d04_sensor_acquisition", f'''
  rankdir=TB;
  a [label="acquire_sensors()", {BLUE}, penwidth=2.2];
  b [label="imu.read()", {TEALN}];
  c [label="valid and finite?", {DIAM}];
  d [label="within datasheet bounds?\\naccel < 170 m/s² · gyro < 2200 °/s", {DIAM}];
  e [label="reject sample · DROP previous value\\nraise sensor_implausible", {REDN}];
  f [label="feed calibrator with RAW sample\\nsubtract gyro & accel bias", {BLUE}];
  g [label="orientation.update(dt)\\nMahony quaternion filter", {BLUE}];
  h [label="snapshot ax ay az · roll pitch yaw", {GREENN}];
  s [label="no good read for > 2000 ms?", {DIAM}];
  s2 [label="imu_valid = false\\nraise imu_stale + orientation_invalid", {REDN}];
  s3 [label="keep last good value", {GREY}];
  j [label="baro.read()", {TEALN}];
  k [label="valid · 30–115 kPa · −50…95 °C?", {DIAM}];
  l [label="stale check\\nbaro_stale after 2000 ms", {GREY}];
  m [label="AGL = altitude − ground baseline\\nvertical rate: EWMA 0.7 old + 0.3 new", {BLUE}];
  o [label="gps.latest()\\nfix used only while it is being renewed", {TEALN}];
  a -> b -> c; c -> d [label="yes"]; c -> s [label="no"];
  d -> e [label="no"]; d -> f [label="yes"]; f -> g -> h;
  s -> s2 [label="yes"]; s -> s3 [label="no"];
  h -> j; e -> j; s2 -> j; s3 -> j;
  j -> k; k -> m [label="yes"]; k -> l [label="no"]; m -> o; l -> o;
''')

    # ---- 5  state machine --------------------------------------------------------------
    dot("d05_state_machine", f'''
  rankdir=TB; nodesep=0.5; ranksep=0.55;
  init [label="INIT", {GREY}];
  st [label="SELF_TEST\\nmandatory sensors\\nproduce valid data", {BLUE}];
  rd [label="READY\\ncalibrating · listening\\nthen armed", {TEALN}, penwidth=2.2];
  fl [label="FLIGHT\\nreleased · descending", {GOLDN}, penwidth=2.2];
  ld [label="LANDED\\n5 s post-impact window", {GREENN}];
  rc [label="RECOVERY\\ntelemetry continues", {GREENN}];
  ft [label="FAULT\\ntransmission never stops", {REDN}];
  init -> st [label="begin_self_test"];
  st -> rd [label="sensors OK"];
  rd -> fl [label="armed AND (accel > 30 m/s² OR climb > 15 m)\\nheld 300 ms"];
  fl -> ld [label="descent observed (< −2 m/s for 1 s)\\nTHEN at rest, |rate| < 1 m/s, 3 s"];
  ld -> rc [label="5 s elapsed"];
  st -> ft [style=dashed, color="#D1495B", label="self-test failed", fontcolor="#D1495B"];
  rd -> ft [style=dashed, color="#D1495B", label="critical fault", fontcolor="#D1495B"];
  fl -> ft [style=dashed, color="#D1495B", fontcolor="#D1495B"];
''')

    # ---- 6  detection logic ------------------------------------------------------------
    dot("d06_detection_logic", f'''
  rankdir=TB;
  subgraph cluster_l {{ label="LAUNCH DETECTION  (READY → FLIGHT)"; fontname="Inter"; fontsize=11; fontcolor="#1D4ED8"; style="rounded"; color="#93C5FD";
    l0 [label="each sample in READY", {BLUE}];
    l1 [label="armed?\\n3 s arming delay elapsed\\nAND calibration settled", {DIAM}];
    l2 [label="accel > 30 m/s²\\nOR climb > 15 m above pad?", {DIAM}];
    l3 [label="held continuously 300 ms?", {DIAM}];
    l4 [label="→ FLIGHT", {GOLDN}, penwidth=2.2];
    l5 [label="ignored\\n(start-up glitch cannot launch)", {GREY}];
    l0 -> l1; l1 -> l2 [label="yes"]; l1 -> l5 [label="no"]; l2 -> l3 [label="yes"]; l3 -> l4 [label="yes"];
  }}
  subgraph cluster_d {{ label="LANDING DETECTION  (FLIGHT → LANDED)  ·  the descent gate"; fontname="Inter"; fontsize=11; fontcolor="#2E9E5B"; style="rounded"; color="#86EFAC";
    d0 [label="each sample in FLIGHT", {BLUE}];
    d1 [label="vertical rate < −2 m/s\\nfor 1 s?", {DIAM}];
    d2 [label="latch: descent_observed\\n(clears on any state change)", {PURP}];
    d3 [label="≥ 3 s into flight?\\n|‖a‖ − g| < 2.5 m/s²\\nAND |vertical rate| < 1 m/s", {DIAM}];
    d4 [label="held 3 s?", {DIAM}];
    d5 [label="→ LANDED\\n5 s post-impact window", {GREENN}, penwidth=2.2];
    d6 [label="a hover is at rest too —\\nwithout descent it cannot land", {GREY}];
    d0 -> d1; d1 -> d2 [label="yes"]; d1 -> d6 [label="no"]; d2 -> d3; d3 -> d4 [label="yes"]; d4 -> d5 [label="yes"];
  }}
''')

    # ---- 7  calibration ----------------------------------------------------------------
    dot("d07_calibration", f'''
  rankdir=TB;
  a [label="accumulate IMU and barometer sums\\n(sum, sum of squares)", {BLUE}];
  b [label="≥ 80 IMU samples?", {DIAM}];
  c [label="per-axis gyro σ and mean |a|", {BLUE}];
  d [label="σ < 2 °/s on every axis\\nAND |a| within 1.5 m/s² of 1 g?", {DIAM}];
  e [label="COMPLETE\\ngyro bias · accel offset ·\\nbarometric ground reference", {GREENN}, penwidth=2.2];
  f [label="discard window, keep sampling", {GREY}];
  g [label="20 s elapsed?", {DIAM}];
  h [label="BEST EFFORT\\nbarometric reference still used\\nbias NOT applied · warning raised", {GOLDN}];
  i [label="controller applies bias\\nresets orientation estimator", {BLUE}];
  a -> b; b -> c [label="yes"]; b -> g [label="no"]; c -> d; d -> e [label="yes"]; d -> f [label="no"]; f -> g;
  g -> h [label="yes"]; g -> a [label="no"]; e -> i; h -> i;
''')

    # ---- 8  telemetry generation ------------------------------------------------------
    dot("d08_telemetry_build", f'''
  rankdir=TB;
  a [label="emit_telemetry()", {BLUE}, penwidth=2.2];
  b [label="candidate = packet_number + 1", {GREY}];
  c [label="append GP- · SN- · ST- on a rich packet", {TEALN}];
  d [label="TelemetryBuilder::build()", {BLUE}];
  e [label="all mandatory fields valid & finite?\\nteam id registered?", {DIAM}];
  f [label="no packet produced\\nnumber NOT consumed\\nraise telemetry_suppressed", {REDN}];
  g [label="size ≤ 200 B?\\nelse shed ST- → SN- → GP-", {DIAM}];
  h [label="packet_number = candidate", {GREENN}];
  i [label="transmit_with_recovery()", {REDN}];
  j [label="append row to SD log", {PURP}];
  a -> b -> c -> d -> e; e -> f [label="no"]; e -> g [label="yes"]; g -> h; h -> i -> j;
''')

    # ---- 9  radio recovery -------------------------------------------------------------
    dot("d09_radio_recovery", f'''
  rankdir=TB;
  a [label="transmit_with_recovery(packet)", {BLUE}, penwidth=2.2];
  b [label="inside the back-off window?", {DIAM}];
  c [label="skip this cycle", {GREY}];
  d [label="radio healthy?", {DIAM}];
  e [label="initialize(sync word)", {TEALN}];
  f [label="init ok?", {DIAM}];
  g [label="radio_init error\\nback off 1000 ms", {REDN}];
  h [label="transmit", {BLUE}];
  i [label="sent?", {DIAM}];
  j [label="clear back-off, counters\\nand radio_tx fault", {GREENN}];
  k [label="failures + 1\\n≥ 5 → one bounded re-init,\\nback off 1000 ms", {GOLDN}];
  a -> b; b -> c [label="yes"]; b -> d [label="no"]; d -> e [label="no"]; d -> h [label="yes"];
  e -> f; f -> g [label="no"]; f -> h [label="yes"]; h -> i; i -> j [label="yes"]; i -> k [label="no"];
''')

    # ---- 10  ground pipeline -----------------------------------------------------------
    dot("d10_ground_pipeline", f'''
  rankdir=LR;
  t [label="Transport\\nserial · file · loopback", {GREY}];
  f [label="Frame decoder\\nCRC-16/CCITT", {BLUE}];
  st [label="bridge status\\nkey = value", {GREY}];
  cr [label="CRC event\\nlogged, not parsed", {REDN}];
  p [label="parse_packet()\\nprecision-strict", {BLUE}];
  iv [label="invalid event\\nlogged with reason", {REDN}];
  v [label="StreamValidator\\nteam · sequence · duplicates ·\\nmonotonic clock · GPS sanity", {PURP}];
  h [label="LinkHealth\\nrate · loss % · staleness", {TEALN}];
  l [label="PacketLog\\nraw .tsv + parsed .csv", {TEALN}];
  s [label="thread-safe snapshot", {GREENN}];
  u [label="Tk dashboard · web console · CLI", {GREENN}, penwidth=2];
  t -> f; f -> st [label="status"]; f -> cr [label="crc fail"]; f -> p [label="payload"];
  p -> iv [label="reject"]; p -> v [label="record"]; v -> h; v -> l; v -> s; h -> s; s -> u;
''')

    # ---- 11  command window ------------------------------------------------------------
    dot("d11_command_window", f'''
  rankdir=TB;
  p [label="POWER ON\\nLED lights · telemetry begins at once", {GOLDN}, penwidth=2.2];
  w [label="COMMAND WINDOW  (0 – 300 s)\\n1.43 Hz telemetry · listens between packets\\ncalibrates once · does not arm", {BLUE}];
  q [label="MAX_RATE accepted\\nOR 300 s elapsed", {DIAM}];
  r [label="discard power-on calibration\\nrecalibrate where it now sits (the pad)", {PURP}];
  m [label="max-rate pattern  3.1 Hz\\nrich · lean · lean  (374 + 296 + 296 ms)\\nuplink closed for the rest of the power cycle", {TEALN}];
  a [label="ARMED  (3 s after close, calibration settled)\\nST-R11x  →  launch detection live", {GREENN}, penwidth=2.2];
  f [label="FLIGHT → LANDED → RECOVERY\\n(uplink stays closed)", {GREENN}];
  wd [label="WATCHDOG RESET  (2 s)\\nskips the window: max rate, closed uplink, re-arms at once", {REDN}];
  p -> w -> q; q -> r [label="first"]; r -> m -> a -> f;
  wd -> m [style=dashed, color="#D1495B"];
''')

    # ---- 12  power path ----------------------------------------------------------------
    dot("d12_power_path", f'''
  rankdir=LR; nodesep=0.28;
  bat [label="LiPo 1S\\n3.7 V (4.2 V full)\\n1500 mAh · 25C", {GOLDN}];
  sw [label="ON/OFF\\nswitch", {GOLDN}];
  vsys [label="Pico VSYS", {BLUE}, penwidth=2];
  reg [label="Pico on-board regulator\\n3V3(OUT)  measured\\n3.28–3.30 V under load", {BLUE}, penwidth=2.2];
  led [label="1 kΩ → red power LED\\n(on the regulated rail)", {REDN}];
  i2c [label="MPU-6500 · BMP280\\nI²C0  GP4/GP5", {TEALN}];
  spi [label="SX1278 · microSD\\nSPI0  GP16/18/19", {TEALN}];
  uart [label="NEO-6M\\nUART0  GP12/GP13", {TEALN}];
  adc [label="LM393 mic  GP27 (ADC1)\\nbattery sense GP26 (33k/33k)", {TEALN}];
  bat -> sw -> vsys -> reg;
  reg -> led; reg -> i2c; reg -> spi; reg -> uart; reg -> adc;
  sw -> adc [style=dashed, label="divider ÷2", constraint=false];
''')

    # ---- 13  SD log layout -------------------------------------------------------------
    dot("d13_sd_layout", f'''
  rankdir=LR; node [shape=record, style="filled", fillcolor="#EFF6FF", color="#1D4ED8"];
  s [label="{{base+0 | header copy A\\nmagic 'CSAT' · version · block size ·\\nnext free block · boot count · sequence · checksum}} | {{base+1 | header copy B\\n(alternates with A — a torn write\\ncan damage only one)}} | {{base+2 … N | one space-padded, newline-terminated\\nrecord per 512-byte block\\n(packet text + full-precision GPS, HDOP,\\nsatellites, sound gate, fault total)}}", fillcolor="#EDE9FE", color="#7B2CBF"];
''')

    # ---- 14  organisation of the deliverable repository --------------------------------
    dot("d14_verification_flow", f'''
  rankdir=LR;
  a [label="Datasheet / rulebook\\nrequirement", {GREY}];
  b [label="Constant or rule in code\\n(source named in a comment)", {BLUE}];
  c [label="Host test\\n(6132 checks)", {PURP}];
  d [label="Bench measurement\\n(bring-up record)", {TEALN}];
  e [label="Flight\\n(30 Sep 2026)", {GREENN}, penwidth=2.2];
  f [label="Documentation checker\\n(numbers in prose = numbers in code)", {GOLDN}];
  a -> b -> c -> d -> e; b -> f [style=dashed]; c -> f [style=dashed];
''')


# ------------------------------------------------------------------------------------------
# matplotlib charts
# ------------------------------------------------------------------------------------------

def mission_profile():
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    # schematic profile: pad -> lift -> hover -> release -> descent -> landing -> recovery
    t = [0, 2, 8, 12, 13.0, 14.0, 21.5, 26.5]
    h = [0, 0, 29.4, 29.4, 30.7, 25.5, 0, 0]
    ax.fill_between(t, h, color=SKY, alpha=0.25, lw=0)
    ax.plot(t[:4], h[:4], color=NAVY, lw=2.2)
    ax.plot(t[3:], h[3:], color=NAVY, lw=2.2)
    ax.axhline(30.48, color=RED, lw=1.0, ls="--")
    ax.text(0.2, 31.2, "100 ft = 30.48 m", color=RED, fontsize=7.4)
    marks = [(1, 1.2, "1  power on\\ntelemetry begins"), (3.4, 14, "2  carried up the building\\naltitude tracked"), (11.4, 33, "3  thrown from the terrace"),
             (13.5, 33.0, ""), (14.0, 22.5, "4  canopy opens"), (18, 14, "5  steady descent\\n≈ 2 m/s"), (22.5, 4, "6  landing"),
             (25, 8.0, "7  post-impact\\ntelemetry · recovery")]
    for x, y, s in marks:
        if s:
            ax.text(x, y, s.replace("\\n", "\n"), fontsize=7.4, color=INK, ha="left" if x < 20 else "center", va="bottom", fontweight="bold" if s[0].isdigit() else "normal")
    ax.set_xlim(0, 28); ax.set_ylim(-2, 38)
    ax.set_xlabel("mission phase (schematic time axis — descent segment drawn to the Flight 1 measurement)")
    ax.set_ylabel("height above launch point (m)")
    ax.set_title("Mission profile")
    ax.set_xticks([])
    _save(fig, FIG, "c01_mission_profile.png")


def mass_budget():
    fig, ax = plt.subplots(figsize=(7.4, 2.8))
    parts = [("Avionics board\n110.6 g", 110.573, NAVY), ("LiPo\n40.7 g", 40.726, GOLD), ("Printed structure\n+ egg chamber\n≈ 128.7 g", 128.7, TEAL),
             ("Canopy, lines, harness 30–55 g", 42.5, F1C), ("Switch, LED, divider 5–10 g", 7.5, PURPLE)]
    x = 0
    for lab, w, c in parts:
        ax.barh(0, w, left=x, color=c, height=0.5, edgecolor="white", lw=1.5)
        if w > 60:
            ax.text(x + w / 2, 0, lab, ha="center", va="center", fontsize=6.8, color="white", fontweight="bold")
        else:
            ax.annotate(lab.replace("\n", " "), xy=(x + w / 2, -0.25), xytext=({"LiPo":120,"Canopy":270,"Switch":420}[lab.split()[0].strip(",")], -0.58 if not lab.startswith("Switch") else -0.78), fontsize=6.6, color=c, ha="center", va="top", fontweight="bold",
                        arrowprops=dict(arrowstyle="-", color=c, lw=0.8))
        x += w
    ax.barh(0, 550 - x, left=x, color="#E2E8F0", height=0.5, hatch="///", edgecolor="#CBD5E1")
    ax.text((x + 550) / 2, 0, "egg payload / trim mass\nto the band", ha="center", va="center", fontsize=7, color=INK, fontweight="bold")
    ax.axvspan(450, 550, color=GREEN, alpha=0.10, lw=0)
    ax.axvline(500, color=GREEN, lw=1.2, ls="--")
    ax.text(500, 0.46, "500 g target · band 450–550 g", ha="center", fontsize=7.4, color=GREEN, fontweight="bold")
    ax.axvline(280, color=INK, lw=1, ls=":")
    ax.text(282, 0.3, "280 g weighed", ha="right", va="bottom", fontsize=7, color=INK)
    ax.set_xlim(0, 580); ax.set_ylim(-0.95, 0.7); ax.set_yticks([])
    ax.set_xlabel("mass (g)"); ax.grid(axis="y", visible=False); ax.spines["left"].set_visible(False)
    ax.set_title("Mass budget")
    _save(fig, FIG, "c02_mass_budget.png")


def airtime_cycle():
    fig, ax = plt.subplots(figsize=(7.4, 2.3))
    seg = [("RICH packet\n374 ms slot", 374, F1C, 0.0), ("lean\n296 ms", 296, TEAL, 0), ("lean\n296 ms", 296, TEAL, 0)]
    x = 0
    air = [323.7, 270.0, 270.0]
    for (lab, w, c, _), a in zip(seg, air):
        ax.barh(0, a, left=x, color=c, height=0.5, edgecolor="white")
        ax.barh(0, w - a, left=x + a, color="#E2E8F0", height=0.5, hatch="///", edgecolor="#CBD5E1")
        ax.text(x + w / 2, 0.42, lab, ha="center", va="bottom", fontsize=7.4, fontweight="bold", color=c)
        x += w
    ax.text(10, 0, "on air", fontsize=6.8, color="white", va="center")
    ax.text(485, -0.38, "hatched = 50 ms guard: SD block write · receiver deaf time", fontsize=6.8, color=MUTED, va="center", ha="center")
    ax.set_xlim(0, 970); ax.set_ylim(-0.5, 1.2); ax.set_yticks([])
    ax.set_xlabel("time within one 966 ms cycle (ms)"); ax.grid(axis="y", visible=False); ax.spines["left"].set_visible(False)
    ax.set_title("Max-rate transmit cycle · 3 packets per 0.966 s = 3.11 Hz")
    _save(fig, FIG, "c03_airtime_cycle.png")


def descent_model():
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.2), gridspec_kw=dict(wspace=0.8))
    D = np.linspace(0.5, 2.3, 90)
    ax = axs[0]
    for m, c in ((0.45, F1C), (0.50, TEAL), (0.55, F2C)):
        for T_c, ls in ((15, "-"), (35, "--")):
            rho = descent.air_density(101325.0, T_c)
            v = [descent.terminal_velocity(m, descent.circular_area(d), 0.75, rho) for d in D]
            ax.plot(D * 100, v, color=c, ls=ls, lw=1.8, label=f"{int(m*1000)} g, {T_c} °C" if True else None)
    ax.axhline(5, color=RED, lw=1.1, ls="--"); ax.text(100, 5.15, "5 m/s limit", color=RED, fontsize=7.4)
    ax.axvline(80, color=MUTED, lw=1.0, ls=":"); ax.text(81, 8.6, "80 cm\nsizing floor", color=MUTED, fontsize=6.8, va="top")
    ax.axvline(182.9, color=GREEN, lw=1.4); ax.text(180, 8.6, "6 ft canopy\nflown", color=GREEN, fontsize=7.2, va="top", ha="right", fontweight="bold")
    ax.scatter([182.9, 182.9], [2.27, 1.88], color=[F1C, F2C], s=60, zorder=5, edgecolor="white")
    ax.text(190, 3.0, "Flight 1\n2.27 m/s", fontsize=6.6, color=F1C, va="center"); ax.text(190, 1.0, "Flight 2\n1.88 m/s", fontsize=6.6, color=F2C, va="center"); ax.set_xlim(45, 260)
    ax.set_xlabel("flat canopy diameter (cm)"); ax.set_ylabel("terminal descent rate (m/s)")
    ax.set_title("Model (vented flat, Cd 0.75) and the flights"); ax.legend(fontsize=5.6, ncol=2, loc="upper center", bbox_to_anchor=(0.62, 0.78))
    ax.set_ylim(0, 9)
    ax = axs[1]
    cds = {"Cruciform 0.85": 0.85, "Flat circular 0.80": 0.80, "Vented flat 0.75": 0.75, "Hemisph. 1.40": 1.40}
    rho = descent.air_density(101325.0, 15)
    names = list(cds); vals = []
    for n, cd in cds.items():
        a = descent.required_area(0.5, 5.0, cd, rho)
        vals.append(100 * descent.circular_diameter(a))
    ax.barh(names, vals, color=[TEAL, F1C, NAVY, PURPLE], height=0.55, zorder=3)
    for i, v in enumerate(vals):
        ax.text(v + 1, i, f"{v:.1f} cm", va="center", fontsize=7.6, fontweight="bold")
    ax.set_xlim(0, 90); ax.set_xlabel("diameter for 5 m/s at 500 g, ISA (cm)"); ax.set_title("Canopy type sets the size")
    ax.grid(axis="y", visible=False)
    _save(fig, FIG, "c04_descent_model.png")


def safety_factors():
    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    names = ["1 · Horizontal\n30 N", "2 · Tearing\n30 N", "3 · Impact\n100 N"]
    iso = [18.9, 40.9, 23.2]; d70 = [13.2, 28.6, 16.2]; d40 = [7.6, 16.4, 9.3]
    x = np.arange(3); w = 0.26
    for k, (v, c, lab) in enumerate(((iso, F1C, "isotropic"), (d70, TEAL, "× 0.70 layer-adhesion derating"), (d40, GOLD, "× 0.40 worst-case derating"))):
        b = ax.bar(x + (k - 1) * w, v, w, color=c, label=lab, zorder=3)
        for xi, vi in zip(x + (k - 1) * w, v):
            ax.text(xi, vi + 0.6, f"{vi:.1f}", ha="center", fontsize=7.2, fontweight="bold")
    ax.axhline(1.0, color=RED, lw=1, ls="--"); ax.text(-0.45, 1.6, "yield (SF = 1)", color=RED, fontsize=7, ha="left")
    ax.axhline(3.0, color=MUTED, lw=0.8, ls=":")
    ax.set_xticks(x); ax.set_xticklabels(names); ax.set_ylabel("safety factor (yield ÷ von Mises)")
    ax.set_ylim(0, 47); ax.legend(loc="upper left", fontsize=7)
    ax.set_title("Structural safety factor by load case"); ax.grid(axis="x", visible=False)
    _save(fig, FIG, "c05_safety_factors.png")


def test_suites():
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    rows = [("Flight core (143 suites)", 4674, F1C), ("microSD driver", 613, PURPLE), ("Documented claims", 307, GOLD), ("Ground station (Python)", 143, TEAL),
            ("LoRa driver", 168, F2C), ("Web console (Node)", 71, GREEN), ("LoRa airtime (Python)", 49, NAVY), ("Descent model", 40, SKY),
            ("Post-flight analysis", 37, MUTED), ("FAT32 reader", 30, RED)]
    rows = rows[::-1]
    ax.barh([r[0] for r in rows], [r[1] for r in rows], color=[r[2] for r in rows], height=0.62, zorder=3)
    for i, r in enumerate(rows):
        ax.text(r[1] + 40, i, f"{r[1]:,}", va="center", fontsize=7.6, fontweight="bold")
    ax.set_xscale("symlog", linthresh=100); ax.set_xlim(0, 12000)
    ax.set_xlabel("automated checks passing (log scale)")
    ax.set_title("6,132 automated checks, all passing"); ax.grid(axis="y", visible=False)
    _save(fig, FIG, "c06_test_suites.png")


def timeline():
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    rows = [("Software stack, host-tested", 3, 4.9, F1C), ("Second review pass — 9 defects fixed", 4, 5.0, NAVY), ("Parts arrive & identified", 4.5, 6.0, TEAL),
            ("Breakout bring-up", 5, 6.0, GOLD), ("Board design & build; first link", 6, 8.0, PURPLE), ("Mission analysis, 1.43 Hz telemetry", 8, 9.0, F2C),
            ("Mechanical design, PETG, 3 stress studies", 9, 10.0, GREEN), ("Range test, 0xA5 sync, max-rate", 10, 12.0, TEAL),
            ("Print, assemble, weigh", 12, 13.0, NAVY), ("Canopy, switch, trim to mass band", 13, 14.9, F1C)]
    for i, (lab, a, b, c) in enumerate(rows[::-1]):
        ax.barh(i, b - a, left=a, color=c, height=0.55, zorder=3)
        ax.text(a - 0.1, i, lab, ha="right", va="center", fontsize=7.4)
    ax.axvline(15, color=RED, lw=1.2, ls="--"); ax.text(15.05, len(rows) - 0.5, "submitted\n14 Sep", color=RED, fontsize=7.2, va="top")
    ax.set_xlim(-6, 16.5); ax.set_xticks(range(3, 16)); ax.set_xticklabels([f"{d}" for d in range(3, 16)], fontsize=7)
    ax.set_xlabel("September 2026"); ax.set_yticks([]); ax.grid(axis="y", visible=False); ax.spines["left"].set_visible(False)
    ax.set_title("Twelve days from first line of code to a built vehicle")
    _save(fig, FIG, "c07_timeline.png")


def packet_anatomy():
    fig, ax = plt.subplots(figsize=(7.4, 2.7))
    groups = [("identity", "CAN-Team-25; P-1585; ", INK, NAVY), ("clock", "Ti-00:11:12:929; ", INK, F1C), ("altitude · pressure · temperature", "A-27.6; Pr-100884.95; T-31.4; ", INK, TEAL),
              ("attitude", "Ro-62.2; Pi-16.0; Ya-153.1; ", INK, PURPLE), ("acceleration", "AX--2.66; AY-10.51; AZ-4.48; ", INK, GOLD),
              ("GPS", "GP-Lat-21.15994; GP-Lon-72.78813; GP-Alt-42; ", INK, F2C), ("sound", "SN-10.5; ", INK, GREEN), ("status", "ST-F111;", INK, MUTED)]
    full = "".join(g[1] for g in groups)
    n = len(full)
    ax.set_xlim(0, n); ax.set_ylim(-1.6, 2.2); ax.axis("off")
    x = 0
    for lab, s, _, c in groups:
        w = len(s)
        ax.add_patch(plt.Rectangle((x, 0.3), w, 0.9, fc=c, alpha=0.16, ec=c, lw=1.2))
        ax.text(x + w / 2, 0.75, s.strip(), ha="center", va="center", fontsize=5.0 if w > 25 else 5.6, family="JetBrains Mono", color=INK)
        ax.text(x + w / 2, 1.45, lab, ha="center", va="bottom", fontsize=6.6, color=c, fontweight="bold")
        ax.text(x + w / 2, 0.0, f"{w} B", ha="center", va="top", fontsize=6.6, color=c)
        x += w
    ax.annotate("", xy=(0, -0.7), xytext=(n, -0.7), arrowprops=dict(arrowstyle="<->", color=MUTED, lw=1))
    ax.text(n / 2, -0.95, f"{n} bytes of text — this packet as received  ·  the organizers' receiver accepts up to 200", ha="center", fontsize=7.2, color=MUTED)
    ax.text(0, 2.05, "mandatory fields (rulebook order)", fontsize=0.1)
    _save(fig, FIG, "c08_packet_anatomy.png")


def link_budget():
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    d = np.logspace(1, 3.4, 100)   # 10 m .. 2.5 km
    fspl = 32.45 + 20 * np.log10(433) + 20 * np.log10(d / 1000)
    pr = 17 - fspl
    ax.plot(d, pr, color=F1C, lw=2, label="free-space prediction (17 dBm, 0 dBi)")
    ax.axhline(-123, color=RED, lw=1.2, ls="--"); ax.text(11, -121.5, "SX127x SF7 / 125 kHz sensitivity ≈ −123 dBm", color=RED, fontsize=7.4, va="bottom")
    ax.axhspan(-109, -79, color=GOLD, alpha=0.22, lw=0)
    ax.text(2300, -94, "measured in flight\n−109 … −79 dBm", color="#9A6B00", fontsize=7.4, ha="right", va="center", fontweight="bold")
    ax.set_xscale("log"); ax.set_xlabel("distance (m)"); ax.set_ylabel("received power (dBm)")
    ax.set_title("Link budget — prediction against the flights"); ax.legend(loc="upper right", fontsize=7)
    ax.set_ylim(-130, -20)
    _save(fig, FIG, "c09_link_budget.png")


def power_budget():
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.0), gridspec_kw=dict(wspace=0.35, width_ratios=[1.3, 1]))
    ax = axs[0]
    items = [("SX1278 TX (17 dBm)", 87, 0.33, F2C), ("microSD write", 100, 0.01, PURPLE), ("NEO-6M tracking", 45, 1.0, TEAL), ("Microphone module", 5, 1.0, GREEN),
             ("MPU-6500", 4, 1.0, F1C), ("BMP280", 1, 1.0, NAVY), ("LEDs ×2", 2.6, 1.0, GOLD), ("SX1278 RX", 12, 0.67, SKY)]
    items.sort(key=lambda r: r[1] * r[2])
    ax.barh([i[0] for i in items], [i[1] * i[2] for i in items], color=[i[3] for i in items], height=0.6, zorder=3)
    for k, i in enumerate(items):
        ax.text(i[1] * i[2] + 0.8, k, f"{i[1]*i[2]:.1f} mA", va="center", fontsize=7)
    ax.set_xlabel("duty-weighted mean draw (mA)"); ax.set_title("Where the current goes"); ax.grid(axis="y", visible=False)
    ax = axs[1]
    cases = [("Steady\nflight", 130), ("GPS\nacquiring", 281), ("Worst\nsimultaneous", 306)]
    ax.bar([c[0] for c in cases], [c[1] for c in cases], color=[GREEN, GOLD, F2C], width=0.6, zorder=3)
    for k, c in enumerate(cases):
        ax.text(k, c[1] + 6, f"{c[1]} mA", ha="center", fontsize=7.4, fontweight="bold")
    ax.set_ylim(0, 360); ax.set_ylabel("mA incl. RP2040")
    ax.set_title("Load cases"); ax.grid(axis="x", visible=False)
    ax.text(0.5, -0.32, "1500 mAh ÷ 130 mA ≈ 11 h of flight-state running", transform=ax.transAxes, ha="center", fontsize=7, color=MUTED)
    _save(fig, FIG, "c10_power_budget.png")


def envelope():
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.6), gridspec_kw=dict(width_ratios=[1, 1.05], wspace=0.25))
    ax = axs[0]
    ax.add_patch(plt.Rectangle((0, 0), 120, 210, fc="#F1F5F9", ec=MUTED, lw=1.2, ls="--"))
    ax.add_patch(plt.Rectangle((0, 210), 120, 70, fc="#FFF7E6", ec=GOLD, lw=1.2, ls="--"))
    ax.add_patch(plt.Rectangle((2.5, 0), 115, 118.5, fc="#DBEAFE", ec=F1C, lw=2))
    ax.text(60, 59, "Cansat_D1\n115 × 118.5 mm", ha="center", va="center", fontsize=7.2, color=F1C, fontweight="bold")
    ax.text(60, 245, "egg-chamber\nallowance +70 mm", ha="center", va="center", fontsize=7.2, color="#9A6B00")
    ax.text(60, 165, "210 mm body allowance\n91.5 mm in reserve", ha="center", va="center", fontsize=7.2, color=MUTED)
    ax.set_xlim(-12, 132); ax.set_ylim(-14, 290); ax.set_aspect("equal"); ax.set_title("Elevation"); ax.set_xlabel("mm"); ax.grid(False)
    ax = axs[1]
    ax.add_patch(plt.Rectangle((0, 0), 120, 120, fc="#F1F5F9", ec=MUTED, lw=1.2, ls="--"))
    ax.add_patch(plt.Rectangle((2.5, 5), 115, 110, fc="#DBEAFE", ec=F1C, lw=2))
    ax.add_patch(plt.Rectangle((7.5, 10), 100, 100, fc="#CCFBF1", ec=TEAL, lw=1.4))
    ax.text(60, 60, "100 × 100 mm\nboard fits flat", ha="center", va="center", fontsize=7.4, color=TEAL, fontweight="bold")
    ax.text(60, 123.5, "120 × 120 mm section limit (organizers confirmed a sided box)", ha="center", fontsize=6.2, color=MUTED)
    ax.set_xlim(-5, 125); ax.set_ylim(-5, 130); ax.set_aspect("equal"); ax.set_title("Section, looking down"); ax.set_xlabel("mm"); ax.grid(False)
    _save(fig, FIG, "c11_envelope.png")


def charts():
    mission_profile(); mass_budget(); airtime_cycle(); descent_model(); safety_factors(); test_suites(); timeline()
    packet_anatomy(); link_budget(); power_budget(); envelope()


if __name__ == "__main__":
    diagrams()
    charts()
