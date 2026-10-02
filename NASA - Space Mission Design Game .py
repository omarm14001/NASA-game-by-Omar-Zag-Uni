#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MISSION ARCHITECT  -  design, launch and operate a complete space mission.

Run:   python mission_architect.py
Needs: Python 3.8+ with Tkinter (included with the standard Python installers).
All graphics are drawn with code - no images, no extra libraries.

THE GAME
  1. Pick a mission (Earth observation, Moon, Mars or Jupiter/Europa).
  2. DESIGN the spacecraft: launcher, power (solar / RTG / battery), propulsion and
     propellant, antenna + transmitter + recorder, science instruments, radiation
     hardening and redundancy.  Live gauges show mass, cost, delta-v (rocket equation),
     power, downlink data rate and expected science versus the mission goal.
  3. LAUNCH (a real chance of failure), CRUISE and fire the orbit-insertion burn.
  4. OPERATE week by week: switch instruments on/off to fit the power budget, keep
     data flowing to Earth, use SAFE MODE against solar storms, run diagnostics,
     watch propellant for station-keeping and cope with random anomalies.
  5. Get a mission report explaining which trade-offs helped or hurt.
"""
import math
import random
import tkinter as tk
from tkinter import messagebox

G0 = 9.80665
BUS_MASS = 90.0
BG, PANEL, FG = "#0a0f1f", "#131a33", "#dbe4ff"
ACC, GOOD, WARN, BAD = "#5ad1ff", "#4cd97b", "#ffcf4a", "#ff5c5c"
F9, F10, FB = ("Helvetica", 9), ("Helvetica", 10), ("Helvetica", 10, "bold")

# --------------------------------------------------------------------------
#  DATA
# --------------------------------------------------------------------------
MISSIONS = {
    "leo": dict(
        title="TERRA-WATCH", sub="Earth observation from low Earth orbit", body="Earth", budget=260.0,
        sun=1.0, ecl=0.35, ecl_h=0.6, dv_ins=0.10, dv_sk=0.010, ops=26, transit=1, deadline=6,
        contact=1.5, link_range=0.1, link_cap=30000, dscale=1.0, rad=0.3, heater=0, lf=1.0, drift=3,
        goal=700, stars=1,
        desc="Map crops, forests and climate. Huge data volumes, brutal eclipses every\n"
             "90 minutes, and atmospheric drag that keeps stealing your orbit."),
    "moon": dict(
        title="SELENE-X", sub="Lunar polar orbiter hunting for water ice", body="Moon", budget=420.0,
        sun=1.0, ecl=0.30, ecl_h=0.9, dv_ins=0.90, dv_sk=0.008, ops=26, transit=1, deadline=10,
        contact=6.0, link_range=0.2, link_cap=4000, dscale=0.7, rad=0.6, heater=20, lf=0.30, drift=4,
        goal=800, stars=2,
        desc="Enter lunar orbit and map ice at the poles. Lumpy gravity makes the orbit\n"
             "unstable, so you need propellant reserved for station-keeping."),
    "mars": dict(
        title="ARES ORBITER", sub="Mars climate and subsurface-ice orbiter", body="Mars", budget=700.0,
        sun=1.52, ecl=0.20, ecl_h=0.8, dv_ins=1.35, dv_sk=0.003, ops=26, transit=40, deadline=60,
        contact=8.0, link_range=1.5, link_cap=6000, dscale=0.15, rad=0.5, heater=40, lf=0.22, drift=8,
        goal=1100, stars=3,
        desc="A 9-month cruise, a big capture burn, and a weak Martian sun. Your\n"
             "antenna and transmitter decide how much data ever reaches Earth."),
    "jup": dict(
        title="EUROPA EXPLORER", sub="Jupiter-system orbiter studying Europa's ice", body="Jupiter", budget=1500.0,
        sun=5.2, ecl=0.10, ecl_h=0.5, dv_ins=1.50, dv_sk=0.004, ops=26, transit=156, deadline=200,
        contact=8.0, link_range=5.2, link_cap=500, dscale=0.02, rad=3.0, heater=100, lf=0.13, drift=6,
        goal=480, stars=4,
        desc="The hardest mission: faint sunlight (1/27 of Earth's), a 3-year cruise, a\n"
             "tiny data link and the harshest radiation in the solar system."),
}
LAUNCHERS = [
    dict(name="Small Launcher", cap=450, cost=14.0, rel=0.90),
    dict(name="Medium Launcher", cap=2600, cost=55.0, rel=0.94),
    dict(name="Heavy Launcher", cap=9000, cost=115.0, rel=0.96),
    dict(name="Super-Heavy", cap=22000, cost=270.0, rel=0.97),
]
PROP = {
    "mono": dict(name="Hydrazine mono", isp=230, mass=12, cost=3.0, tank=0.09, rel=0.985, thrust=400.0, power=0),
    "bi": dict(name="Bipropellant", isp=320, mass=30, cost=9.0, tank=0.08, rel=0.965, thrust=1000.0, power=0),
    "ion": dict(name="Xenon ion", isp=1900, mass=55, cost=18.0, tank=0.15, rel=0.98, thrust=0.05, power=800),
}
RECORDERS = [dict(gb=16, mass=2, cost=1.0), dict(gb=64, mass=4, cost=3.0),
             dict(gb=256, mass=8, cost=8.0), dict(gb=1024, mass=15, cost=20.0)]
HARDEN = [dict(name="None", mass=0.0, cost=0.0, factor=1.0),
          dict(name="Standard", mass=0.05, cost=8.0, factor=0.5),
          dict(name="Heavy vault", mass=0.12, cost=25.0, factor=0.15)]
REDUND = [dict(name="Single string", mass=0.0, cost=0.0, factor=1.0),
          dict(name="Partial", mass=0.04, cost=6.0, factor=0.55),
          dict(name="Full backup", mass=0.09, cost=18.0, factor=0.25)]
INSTR = {
    "cam": dict(name="Visible Camera", mass=25, power=40, data=80, cost=18, sci=10, color="#7fd0ff",
                rel=dict(leo=1.0, moon=0.8, mars=0.9, jup=0.5)),
    "hyp": dict(name="Hyperspectral Imager", mass=45, power=70, data=200, cost=40, sci=20, color="#c78bff",
                rel=dict(leo=1.0, moon=0.9, mars=1.0, jup=0.6)),
    "rad": dict(name="Ice-Sounding Radar", mass=90, power=250, data=400, cost=70, sci=30, color="#ff9a5a",
                rel=dict(leo=0.9, moon=0.8, mars=1.0, jup=1.0)),
    "mag": dict(name="Magnetometer", mass=5, power=5, data=1, cost=5, sci=4, color="#7dffb0",
                rel=dict(leo=0.3, moon=0.4, mars=0.6, jup=1.0)),
    "pla": dict(name="Plasma Spectrometer", mass=12, power=15, data=3, cost=8, sci=6, color="#ffe066",
                rel=dict(leo=0.3, moon=0.4, mars=0.6, jup=1.0)),
    "lid": dict(name="Laser Altimeter", mass=30, power=60, data=20, cost=25, sci=14, color="#ff6b6b",
                rel=dict(leo=0.5, moon=1.0, mars=0.9, jup=0.6)),
    "irs": dict(name="IR Atmosphere Sounder", mass=35, power=50, data=60, cost=28, sci=16, color="#f78fb3",
                rel=dict(leo=1.0, moon=0.2, mars=1.0, jup=0.7)),
}
INSTR_ORDER = ["cam", "hyp", "rad", "mag", "pla", "lid", "irs"]


# --------------------------------------------------------------------------
#  DESIGN MODEL  (pure logic, no graphics)
# --------------------------------------------------------------------------
class Design:
    def __init__(self, mid):
        self.mid, self.m = mid, MISSIONS[mid]
        self.launcher, self.solar, self.rtg, self.battery = 1, 8.0, 0, 600.0
        self.prop_type, self.prop = "bi", 100.0
        self.dish, self.tx, self.rec = 1.0, 30.0, 1
        self.inst = set()
        self.harden, self.redund = 0, 0

    def compute(self):
        m, P, L, R = self.m, PROP[self.prop_type], LAUNCHERS[self.launcher], RECORDERS[self.rec]
        ins = [INSTR[k] for k in sorted(self.inst)]
        i_mass = sum(i["mass"] for i in ins)
        i_pow = sum(i["power"] for i in ins)
        i_cost = sum(i["cost"] for i in ins)
        i_data = sum(i["data"] for i in ins) * m["dscale"]
        # ---- mass ----
        parts = [("Instruments", i_mass),
                 ("Power system", self.solar * 5 + self.rtg * 45 + self.battery * 0.012),
                 ("Comms", 8 + 3 * self.dish ** 2 + 0.12 * self.tx),
                 ("Data recorder", R["mass"]), ("Bus & avionics", BUS_MASS),
                 ("Propulsion", P["mass"] + P["tank"] * self.prop)]
        sub = sum(x for _, x in parts)
        hard = HARDEN[self.harden]["mass"] * (BUS_MASS + i_mass)
        red = REDUND[self.redund]["mass"] * sub
        struct = 0.12 * (sub + hard + red)
        parts += [("Rad. hardening", hard), ("Redundancy", red), ("Structure", struct)]
        dry = sub + hard + red + struct
        wet = dry + self.prop
        cap = L["cap"] * m["lf"]
        # ---- delta-v (Tsiolkovsky) ----
        ve = P["isp"] * G0
        dv = ve * math.log(wet / dry) / 1000.0
        dv_req = m["dv_ins"] + m["dv_sk"] * m["ops"]
        margin = dv / dv_req if dv_req > 0 else 9.0
        ion_weeks = 0.0
        if self.prop_type == "ion" and self.prop > 0:
            used = wet * (1 - math.exp(-m["dv_ins"] * 1000 / ve))
            ion_weeks = (wet - used / 2) * m["dv_ins"] * 1000 / P["thrust"] / 604800.0
        arrival = m["transit"] + ion_weeks
        # ---- power ----
        flux = 1361.0 / m["sun"] ** 2
        solar_bol = self.solar * 0.28 * flux * 0.85
        rtg_bol = self.rtg * 110.0
        gen = solar_bol * (1 - m["ecl"]) * 0.92 + rtg_bol
        tx_dc = self.tx / 0.35 * m["contact"] / 24.0
        base = 60.0 + m["heater"] + tx_dc
        load = base + i_pow
        bat_need = load * m["ecl_h"] / 0.4 if solar_bol > 0 else 0.0
        ion_ok = self.prop_type != "ion" or (solar_bol + rtg_bol) >= 60 + m["heater"] + P["power"]
        # ---- comms & data ----
        rate = min(m["link_cap"], 3.5 * self.tx * self.dish ** 2 / m["link_range"] ** 2)
        down = rate * m["contact"] * 0.0252
        # ---- science potential ----
        sci_wk = sum(i["sci"] * i["rel"][self.mid] for i in ins)
        duty = 1.0 if i_pow <= 0 else max(0.0, min(1.0, (gen - base) / i_pow))
        dlr = 1.0 if i_data <= 0 else min(1.0, down / i_data)
        sci_pot = sci_wk * m["ops"] * duty * dlr * 0.9
        # ---- cost ($M) ----
        cparts = [("Bus & avionics", 30.0), ("Instruments", i_cost), ("Solar arrays", self.solar * 0.6),
                  ("RTGs", self.rtg * 55.0), ("Battery", self.battery * 0.0015),
                  ("Comms", 1.2 * self.dish ** 2 + 0.06 * self.tx), ("Recorder", R["cost"]),
                  ("Propulsion", P["cost"] + self.prop * 0.004), ("Hardening", HARDEN[self.harden]["cost"]),
                  ("Redundancy", REDUND[self.redund]["cost"]), ("Assembly & test", 0.03 * dry)]
        hardware = sum(x for _, x in cparts)
        integ = 0.3 * hardware
        ops_cost = arrival * 0.1 + m["ops"] * 0.3
        total = hardware + integ + L["cost"] + ops_cost
        reserve = m["budget"] - total
        c = dict(parts=parts, dry=dry, wet=wet, cap=cap, dv=dv, dv_req=dv_req, margin=margin, ion_weeks=ion_weeks,
                 arrival=arrival, solar_bol=solar_bol, rtg_bol=rtg_bol, gen=gen, load=load, base=base,
                 i_pow=i_pow, bat_need=bat_need, ion_ok=ion_ok, rate=rate, down=down, data=i_data,
                 storage=R["gb"], sci_wk=sci_wk, sci_pot=sci_pot, duty=duty, dlr=dlr, cparts=cparts,
                 hardware=hardware, integ=integ, launch=L["cost"], ops_cost=ops_cost, total=total, reserve=reserve)
        checks, blockers = [], []
        add = lambda n, s, t: checks.append((n, s, t))
        if wet > cap:
            add("Launch mass", "fail", "%.0f kg is more than the %.0f kg this launcher can send to this destination" % (wet, cap))
            blockers.append("Spacecraft is too heavy for the launcher")
        else:
            add("Launch mass", "ok", "%.0f kg fits (capacity %.0f kg)" % (wet, cap))
        if reserve < 0:
            add("Budget", "fail", "over budget by $%.0fM" % -reserve)
            blockers.append("Over budget")
        elif reserve < 0.05 * m["budget"]:
            add("Budget", "warn", "only $%.0fM contingency left - no room for surprises" % reserve)
        else:
            add("Budget", "ok", "$%.0fM contingency held in reserve" % reserve)
        if not self.inst:
            add("Payload", "fail", "no science instruments selected")
            blockers.append("Select at least one instrument")
        if margin < 1.0:
            add("Delta-v", "fail", "%.2f km/s available, %.2f needed: you will NOT reach orbit or keep it" % (dv, dv_req))
        elif margin < 1.1:
            add("Delta-v", "warn", "margin only %d%% - thin for insertion errors" % round((margin - 1) * 100))
        else:
            add("Delta-v", "ok", "%.2f km/s vs %.2f needed (+%d%% margin)" % (dv, dv_req, round((margin - 1) * 100)))
        if gen >= load * 1.05:
            add("Power", "ok", "%.0f W generated vs %.0f W with everything on" % (gen, load))
        elif gen >= base + 0.5 * i_pow and i_pow > 0:
            add("Power", "warn", "%.0f W vs %.0f W: you must switch instruments off" % (gen, load))
        else:
            add("Power", "fail", "%.0f W vs %.0f W: severe shortfall" % (gen, load))
        if solar_bol > 0 and self.battery < bat_need:
            add("Battery", "warn", "%.0f Wh installed, ~%.0f Wh needed to ride through eclipse" % (self.battery, bat_need))
        if i_data > 0:
            if down >= i_data:
                add("Data link", "ok", "%.0f Gb/wk downlink vs %.0f Gb/wk produced" % (down, i_data))
            elif down >= 0.5 * i_data:
                add("Data link", "warn", "downlink %.0f < produced %.0f Gb/wk: data will back up" % (down, i_data))
            else:
                add("Data link", "fail", "downlink %.0f Gb/wk but %.0f produced: most data lost" % (down, i_data))
        if not ion_ok:
            add("Ion drive", "fail", "ion thrusters need ~%d W of power to run" % (60 + m["heater"] + P["power"]))
        if ion_weeks > 0:
            add("Schedule", "ok" if arrival <= m["deadline"] else "warn",
                "arrival after %.0f weeks (window %d wks); ion spiral adds %.0f wks" % (arrival, m["deadline"], ion_weeks))
        elif arrival > m["deadline"]:
            add("Schedule", "warn", "arrival after %.0f weeks misses the %d-week window" % (arrival, m["deadline"]))
        if m["rad"] >= 2 and self.harden == 0:
            add("Radiation", "warn", "unhardened electronics will be cooked by this radiation environment")
        if self.redund == 0:
            add("Redundancy", "warn", "single-string design: any anomaly can end the mission")
        if self.inst and sci_pot < 0.7 * m["goal"]:
            add("Science", "warn", "expected %.0f pts vs goal %d: the design cannot reach the goal" % (sci_pot, m["goal"]))
        elif self.inst:
            add("Science", "ok", "expected %.0f pts vs goal %d" % (sci_pot, m["goal"]))
        c["checks"], c["blockers"] = checks, blockers
        return c

    def auto_prop(self, margin=1.12):
        req = self.m["dv_ins"] * margin + self.m["dv_sk"] * self.m["ops"] * margin
        lo, hi = 0.0, 8000.0
        for _ in range(60):
            mid = (lo + hi) / 2
            self.prop = mid
            if self.compute()["dv"] >= req:
                hi = mid
            else:
                lo = mid
        self.prop = float(min(4000, math.ceil(hi / 5.0) * 5))


# --------------------------------------------------------------------------
#  FLIGHT MODEL  (launch, cruise, insertion, weekly operations)
# --------------------------------------------------------------------------
class Flight:
    def __init__(self, design, seed=None):
        self.d, self.m = design, design.m
        self.c = design.compute()
        self.rng = random.Random(seed)
        self.P = PROP[design.prop_type]
        self.dry = self.c["dry"]
        self.prop_left = design.prop
        self.solar_health = self.rtg_health = self.comm_health = 1.0
        self.ih = {k: 1.0 for k in design.inst}
        self.week = 0
        self.forced_safe = 0
        self.storm_warned = False
        self.diag_left = 0
        self.pool_data = self.pool_sci = self.returned = self.lost = 0.0
        self.reserve = self.c["reserve"]
        self.drift = 0
        self.ended = self.alive = self.reached_orbit = False
        self.reason = ""
        self.hist = []
        self.cnt = dict(brownout=0, safe=0, storm=0, inst_fail=0, deploy=0)
        self.last = dict(down=0.0, gen=0.0, load=0.0, safe=False, dl=0.0)

    # ---- pre-operations ----
    def launch(self):
        ok = self.rng.random() < LAUNCHERS[self.d.launcher]["rel"]
        if not ok:
            self.ended = True
            self.reason = "The launch vehicle failed. Even good rockets fail 3-10% of the time - that risk is part of every mission."
        return ok

    def cruise(self):
        out, rng = [], self.rng
        rf = REDUND[self.d.redund]["factor"]
        out.append(("Cruise: %.0f weeks to the target." % self.c["arrival"], "info"))
        if rng.random() < 0.05 * rf:
            self.solar_health *= 0.7
            self.cnt["deploy"] += 1
            out.append(("A solar wing deployed only partially: array output -30%.", "bad"))
        for _ in range(int(self.c["arrival"])):
            if rng.random() < 0.004 * rf:
                self.solar_health *= 0.95
                out.append(("Micrometeoroid strike in cruise: array output -5%.", "warn"))
        if not out[1:]:
            out.append(("Cruise was quiet - all systems healthy.", "good"))
        return out

    def insertion(self):
        m, out = self.m, []
        if not self.c["ion_ok"]:
            self.ended, self.reason = True, "The ion drive was starved of power and the spacecraft never reached its target orbit."
            return False, [("Ion thrusters cannot run: not enough electrical power.", "bad")]
        ve = self.P["isp"] * G0
        used = (self.dry + self.prop_left) * (1 - math.exp(-m["dv_ins"] * 1000 / ve))
        if used > self.prop_left:
            self.prop_left = 0.0
            self.ended = True
            self.reason = "Propellant ran out during orbit insertion: not enough delta-v (the rocket equation always wins)."
            return False, [("Engine cut off - propellant exhausted. Spacecraft flew past the target.", "bad")]
        self.prop_left -= used
        p = self.P["rel"] + (0.01 if self.c["margin"] >= 1.1 else 0.0)
        if self.rng.random() > p:
            self.ended = True
            self.reason = "The main engine failed during the insertion burn. Complex engines fail; simpler ones are more reliable."
            return False, [("Engine anomaly during the burn! Orbit insertion failed.", "bad")]
        self.reached_orbit = self.alive = True
        return True, [("Orbit insertion complete! Used %.0f kg of propellant, %.0f kg left." % (used, self.prop_left), "good")]

    # ---- operations ----
    def power_calc(self, on, safe):
        m, d = self.m, self.d
        solar = d.solar * 0.28 * (1361.0 / m["sun"] ** 2) * 0.85 * self.solar_health
        gen = solar * (1 - m["ecl"]) * 0.92 + d.rtg * 110.0 * self.rtg_health
        base = 60.0 + m["heater"] + d.tx / 0.35 * m["contact"] / 24.0
        inst = 0.0 if safe else sum(INSTR[k]["power"] for k in on if k in self.ih and self.ih[k] > 0.02)
        load = base + inst
        duty = 1.0 if inst <= 0 else max(0.0, min(1.0, (gen - base) / inst))
        need = load * m["ecl_h"] / 0.4 if solar > 0 else 0.0
        bat = 1.0 if need <= 0 else min(1.0, d.battery / need)
        return dict(gen=gen, base=base, inst=inst, load=load, duty=duty * (0.5 + 0.5 * bat), need=need, bat=bat)

    def downlink_capacity(self):
        return self.c["rate"] * self.comm_health * self.m["contact"] * 0.0252

    def step(self, on, safe, diag):
        m, d, rng, out = self.m, self.d, self.rng, []
        hf, rf = HARDEN[d.harden]["factor"], REDUND[d.redund]["factor"]
        self.week += 1
        if diag:
            self.reserve -= 0.5
            self.diag_left = 3
            out.append(("Ground team ran diagnostics (-$0.5M): software glitches suppressed for 3 weeks.", "info"))
        if self.forced_safe > 0:
            self.forced_safe -= 1
            safe = True
        if safe:
            self.cnt["safe"] += 1
            out.append(("SAFE MODE: instruments off this week, downlink continues.", "warn"))
        # solar storm
        if self.storm_warned:
            self.storm_warned = False
            self.cnt["storm"] += 1
            if safe:
                out.append(("Solar storm hit - safe mode protected the payload.", "good"))
            else:
                hit = []
                for k in self.ih:
                    if self.ih[k] > 0 and rng.random() < 0.35 * hf:
                        self.ih[k] *= 0.5
                        hit.append(INSTR[k]["name"])
                self.solar_health *= 1 - 0.08 * hf
                out.append(("SOLAR STORM! Arrays degraded%s." % ((" and damaged: " + ", ".join(hit)) if hit else ""), "bad"))
        elif rng.random() < 0.05 + 0.02 * m["rad"]:
            self.storm_warned = True
            out.append(("WARNING: solar storm arrives next week! Tick SAFE MODE for the coming week.", "warn"))
        # chronic radiation & ageing
        for k in self.ih:
            self.ih[k] = max(0.0, self.ih[k] - 0.006 * m["rad"] * hf * (0.3 if safe else 1.0))
        self.solar_health = max(0.2, self.solar_health * (1 - 0.004 * m["rad"] * hf - 0.0003))
        self.rtg_health *= 0.999
        # random anomalies
        alive_i = [k for k in self.ih if self.ih[k] > 0.05]
        if alive_i and rng.random() < 0.025 * rf * (1 + 0.3 * m["rad"]):
            k = rng.choice(alive_i)
            self.cnt["inst_fail"] += 1
            if rng.random() < 0.5:
                self.ih[k] = 0.0
                out.append(("%s FAILED permanently." % INSTR[k]["name"], "bad"))
            else:
                self.ih[k] *= 0.5
                out.append(("%s degraded to half performance." % INSTR[k]["name"], "bad"))
        if rng.random() < 0.02 * rf:
            if d.redund >= 1:
                out.append(("Transmitter fault - backup amplifier switched in.", "good"))
            else:
                self.comm_health = max(0.3, self.comm_health * 0.75)
                out.append(("Transmitter degraded: downlink capacity -25%.", "bad"))
        if rng.random() < 0.03 * rf:
            n = [3, 1, 0][d.redund]
            if n:
                self.forced_safe += n
                out.append(("Reaction-wheel fault: safe mode for the next %d week(s)." % n, "warn"))
            else:
                out.append(("Reaction wheel fault - backup wheel took over seamlessly.", "good"))
        if self.diag_left > 0:
            self.diag_left -= 1
        elif rng.random() < 0.04:
            self.forced_safe += 1
            out.append(("Software glitch: spacecraft will enter safe mode next week.", "warn"))
        if rng.random() < 0.02:
            self.solar_health *= 0.95
            out.append(("Micrometeoroid hit an array: output -5%.", "warn"))
        # power, science, data
        pc = self.power_calc(on, safe)
        if pc["gen"] < pc["base"]:
            self.forced_safe += 1
            self.cnt["brownout"] += 1
            out.append(("POWER CRISIS: cannot even run the bus. Safe mode forced.", "bad"))
        gen_data = gen_sci = 0.0
        if not safe:
            for k in on:
                if k in self.ih and self.ih[k] > 0.02:
                    e = pc["duty"] * self.ih[k]
                    gen_data += INSTR[k]["data"] * m["dscale"] * e
                    gen_sci += INSTR[k]["sci"] * INSTR[k]["rel"][d.mid] * e
            if pc["inst"] > 0 and pc["duty"] < 0.97:
                self.cnt["brownout"] += 1
                out.append(("Power/battery limits: instruments ran at %d%% duty." % round(pc["duty"] * 100), "warn"))
        self.pool_data += gen_data
        self.pool_sci += gen_sci
        dl = min(self.downlink_capacity(), self.pool_data)
        if self.pool_data > 0:
            frac = dl / self.pool_data
            ret = self.pool_sci * frac
            self.pool_sci -= ret
            self.pool_data -= dl
            self.returned += ret
        cap = RECORDERS[d.rec]["gb"]
        if self.pool_data > cap:
            self.lost += self.pool_data - cap
            self.pool_sci *= cap / self.pool_data
            self.pool_data = cap
            out.append(("Recorder full - data was overwritten and lost!", "bad"))
        # station keeping
        ve = self.P["isp"] * G0
        used = (self.dry + self.prop_left) * (1 - math.exp(-m["dv_sk"] * 1000 / ve))
        if self.prop_left >= used:
            self.prop_left -= used
            self.drift = 0
        else:
            self.drift += 1
            out.append(("No propellant for station-keeping: orbit drifting (%d/%d)." % (self.drift, m["drift"]), "bad"))
        self.hist.append(self.returned)
        self.last = dict(down=dl, gen=pc["gen"], load=pc["load"], safe=safe, dl=dl)
        # end conditions
        if self.drift >= m["drift"]:
            self.ended, self.alive = True, False
            self.reason = "The orbit decayed: no propellant was left for station-keeping."
        elif not any(v > 0.05 for v in self.ih.values()):
            self.ended, self.alive = True, False
            self.reason = "Every science instrument failed."
        elif self.reserve < 0:
            self.ended, self.alive = True, False
            self.reason = "The contingency fund ran out and the mission was cancelled."
        elif self.week >= m["ops"]:
            self.ended = True
            self.reason = "The primary mission is complete."
        return out

    def result(self):
        g = self.m["goal"]
        frac = self.returned / g
        if not self.reached_orbit:
            return "MISSION LOSS", 0, frac
        if frac < 0.05:
            title = "MISSION LOSS"
        elif frac < 0.35:
            title = "PARTIAL SUCCESS"
        elif frac < 0.70:
            title = "MINIMUM SUCCESS"
        elif frac < 1.0:
            title = "SUCCESS"
        elif frac >= 1.3 and self.reserve > 0.1 * self.m["budget"]:
            title = "OUTSTANDING SUCCESS"
        else:
            title = "FULL SUCCESS"
        avg_ih = sum(self.ih.values()) / max(1, len(self.ih))
        late = max(0.0, self.c["arrival"] - self.m["deadline"])
        score = min(frac, 1.5) * 600 + min(100.0, max(0.0, self.reserve) / self.m["budget"] * 400)
        score += 100 * (0.5 * self.solar_health + 0.5 * avg_ih) + max(0.0, 100 - 5 * late)
        return title, int(score), frac


# --------------------------------------------------------------------------
#  DRAWING HELPERS
# --------------------------------------------------------------------------
def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_band(c, cx, cy, r, y1, y2, fill):
    pts = []
    for k in range(13):
        y = y1 + (y2 - y1) * k / 12.0
        pts.append((cx + math.sqrt(max(0, r * r - y * y)), cy + y))
    for k in range(12, -1, -1):
        y = y1 + (y2 - y1) * k / 12.0
        pts.append((cx - math.sqrt(max(0, r * r - y * y)), cy + y))
    c.create_polygon([v for p in pts for v in p], fill=fill, outline="")


def draw_planet(c, cx, cy, r, body, tag="static"):
    o = dict(tags=tag)
    if body == "Earth":
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#1f5fbf", outline="#8fc4ff", **o)
        for dx, dy, w, h in ((-0.45, -0.25, 0.5, 0.35), (0.05, -0.55, 0.4, 0.3), (0.1, 0.1, 0.45, 0.4), (-0.4, 0.3, 0.3, 0.25)):
            c.create_oval(cx + dx * r, cy + dy * r, cx + (dx + w) * r, cy + (dy + h) * r, fill="#3a9d4f", outline="", **o)
        for dx, dy in ((-0.6, 0.0), (0.2, -0.3), (0.0, 0.55)):
            c.create_line(cx + dx * r, cy + dy * r, cx + (dx + 0.35) * r, cy + dy * r - 4, fill="white", width=3, **o)
    elif body == "Moon":
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#b9b9c0", outline="#e5e5ea", **o)
        for dx, dy, rr in ((-0.4, -0.3, 0.16), (0.3, -0.45, 0.1), (0.35, 0.2, 0.2), (-0.2, 0.4, 0.12), (-0.55, 0.1, 0.08)):
            c.create_oval(cx + (dx - rr) * r, cy + (dy - rr) * r, cx + (dx + rr) * r, cy + (dy + rr) * r,
                          fill="#8f8f98", outline="#77777f", **o)
    elif body == "Mars":
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#c1633a", outline="#e9a27a", **o)
        for dx, dy, w, h in ((-0.5, -0.1, 0.5, 0.3), (0.0, 0.2, 0.45, 0.28), (0.1, -0.35, 0.3, 0.2)):
            c.create_oval(cx + dx * r, cy + dy * r, cx + (dx + w) * r, cy + (dy + h) * r, fill="#8d3f22", outline="", **o)
        c.create_oval(cx - 0.3 * r, cy - 0.98 * r, cx + 0.3 * r, cy - 0.7 * r, fill="#f4efe8", outline="", **o)
    else:  # Jupiter
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#d9b38c", outline="#f0d2ae", **o)
        cols = ["#b8875a", "#e7cfaa", "#a5683f", "#eed9b9", "#b8875a"]
        for k, col in enumerate(cols):
            draw_band(c, cx, cy, r * 0.99, -0.8 * r + k * 0.32 * r, -0.8 * r + k * 0.32 * r + 0.16 * r, col)
        c.create_oval(cx + 0.1 * r, cy + 0.2 * r, cx + 0.5 * r, cy + 0.4 * r, fill="#c4472f", outline="", **o)


def draw_spacecraft(c, cx, cy, d, comp, scale=1.0, tag="craft", dim=False):
    s, o = scale, dict(tags=tag)
    gold = "#a8862a" if dim else "#d4a72c"
    w, h = 70 * s, 54 * s
    # solar wings
    if d.solar > 0:
        ww = math.sqrt(d.solar) * 26 * s
        wh = ww / 2
        for sign in (-1, 1):
            x0 = cx + sign * (w / 2 + 8 * s)
            x1 = x0 + sign * ww
            c.create_line(cx + sign * w / 2, cy, x0, cy, fill="#999", width=max(1, int(3 * s)), **o)
            c.create_rectangle(min(x0, x1), cy - wh / 2, max(x0, x1), cy + wh / 2, fill="#1f3f9e", outline="#9bb7ff", **o)
            for k in range(1, 5):
                xx = min(x0, x1) + ww * k / 5
                c.create_line(xx, cy - wh / 2, xx, cy + wh / 2, fill="#5f7fe0", **o)
            c.create_line(min(x0, x1), cy, max(x0, x1), cy, fill="#5f7fe0", **o)
    # bus
    if d.harden:
        pad = (3 + 4 * d.harden) * s
        c.create_rectangle(cx - w / 2 - pad, cy - h / 2 - pad, cx + w / 2 + pad, cy + h / 2 + pad,
                           fill="#6c7280", outline="#c0c6d4", **o)
    c.create_rectangle(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, fill=gold, outline="#5a4310", width=2, **o)
    # tank
    frac = min(1.0, d.prop / max(1.0, comp["wet"]))
    c.create_oval(cx - 14 * s, cy - 14 * s, cx + 14 * s, cy + 14 * s, fill=mix("#333344", "#3ec8ff", frac), outline="#222", **o)
    if d.redund:
        for k in range(d.redund):
            c.create_rectangle(cx + 18 * s, cy - 20 * s + k * 12 * s, cx + 30 * s, cy - 12 * s + k * 12 * s,
                               fill="#e0e0e8", outline="#555", **o)
    # battery
    if d.battery > 0:
        bw = 6 + min(20, d.battery / 150.0)
        c.create_rectangle(cx - w / 2 + 4 * s, cy + h / 2 - 12 * s, cx - w / 2 + (4 + bw) * s, cy + h / 2 - 4 * s,
                           fill="#3fae5a", outline="#1b5e20", **o)
    # dish
    r = (5 + d.dish * 9) * s
    dy = cy - h / 2 - 12 * s
    c.create_line(cx, cy - h / 2, cx, dy, fill="#aaa", width=2, **o)
    c.create_oval(cx - r, dy - r * 0.45, cx + r, dy + r * 0.45, fill="#e8e8ee", outline="#666", **o)
    c.create_line(cx, dy, cx, dy - 10 * s - r * 0.5, fill="#ccc", **o)
    # instruments
    for i, k in enumerate(sorted(d.inst)):
        x = cx - w / 2 + 6 * s + i * 9 * s
        c.create_rectangle(x, cy + h / 2, x + 7 * s, cy + h / 2 + 9 * s, fill=INSTR[k]["color"], outline="#222", **o)
    # rtg
    for i in range(d.rtg):
        y = cy + h / 2 + 12 * s + i * 11 * s
        c.create_line(cx + w / 2, cy + h / 2 - 4 * s, cx + w / 2 + 10 * s, y, fill="#999", **o)
        c.create_rectangle(cx + w / 2 + 10 * s, y - 4 * s, cx + w / 2 + 36 * s, y + 4 * s, fill="#8c8f98", outline="#333", **o)
        c.create_rectangle(cx + w / 2 + 36 * s, y - 3 * s, cx + w / 2 + 40 * s, y + 3 * s, fill="#ff8a3d", outline="", **o)
    # nozzle
    col = {"mono": "#9a9aa0", "bi": "#c08a4a", "ion": "#66ccff"}[d.prop_type]
    c.create_polygon(cx - 7 * s, cy + h / 2 + 10 * s, cx + 7 * s, cy + h / 2 + 10 * s, cx + 11 * s, cy + h / 2 + 24 * s,
                     cx - 11 * s, cy + h / 2 + 24 * s, fill=col, outline="#333", **o)


# --------------------------------------------------------------------------
#  APPLICATION
# --------------------------------------------------------------------------
class App:
    SW, SH = 720, 420

    def __init__(self, root):
        self.root = root
        root.title("MISSION ARCHITECT - Space Mission Design Game")
        root.configure(bg=BG)
        root.geometry("1290x800")
        root.resizable(False, False)
        rs = random.Random(11)
        self.stars = [(rs.randint(0, self.SW), rs.randint(0, self.SH), rs.choice((1, 1, 2))) for _ in range(130)]
        self.frame = None
        self.afters = []
        self.flight = None
        self.design = None
        self.ready = False
        self.stage = ""
        self.ang = 0.0
        self.show_select()

    # ---- infrastructure ----
    def later(self, ms, fn):
        self.afters.append(self.root.after(ms, fn))

    def clear(self):
        for a in self.afters:
            try:
                self.root.after_cancel(a)
            except Exception:
                pass
        self.afters = []
        self.ready = False
        self.stage = ""
        if self.frame:
            self.frame.destroy()
        f = tk.Frame(self.root, bg=BG)
        f.pack(fill="both", expand=True)
        self.frame = f
        return f

    def starfield(self, c, w=None, h=None, tag="static"):
        for x, y, s in self.stars:
            c.create_oval(x, y, x + s, y + s, fill="white", outline="", tags=tag)

    # ==================================================================== SELECT
    def show_select(self):
        self.flight = None
        f = self.clear()
        tk.Label(f, text="MISSION ARCHITECT", font=("Helvetica", 30, "bold"), fg=ACC, bg=BG).pack(pady=(14, 0))
        tk.Label(f, text="Design it. Launch it. Fly it. Every choice is a trade-off between mass, power, data and money.",
                 font=("Helvetica", 12), fg=FG, bg=BG).pack()
        grid = tk.Frame(f, bg=BG)
        grid.pack(pady=12)
        for i, mid in enumerate(("leo", "moon", "mars", "jup")):
            m = MISSIONS[mid]
            card = tk.Frame(grid, bg=PANEL, padx=10, pady=8)
            card.grid(row=i // 2, column=i % 2, padx=12, pady=8)
            cv = tk.Canvas(card, width=420, height=150, bg="black", highlightthickness=0)
            cv.pack()
            rs = random.Random(i)
            for _ in range(70):
                x, y = rs.randint(0, 420), rs.randint(0, 150)
                cv.create_oval(x, y, x + 1, y + 1, fill="white", outline="")
            r = 48 if m["body"] != "Jupiter" else 62
            draw_planet(cv, 300, 78, r, m["body"], "art")
            cv.create_oval(300 - r - 22, 78 - r * 0.5 - 12, 300 + r + 22, 78 + r * 0.5 + 12, outline="#5ad1ff", dash=(3, 3))
            cv.create_rectangle(300 + r + 18, 72, 300 + r + 30, 80, fill="#d4a72c", outline="")
            cv.create_text(12, 12, anchor="nw", text=m["title"], fill="white", font=("Helvetica", 16, "bold"))
            cv.create_text(12, 40, anchor="nw", text=m["sub"], fill="#9fb4ff", font=F9, width=170)
            tk.Label(card, text="Budget $%.0fM   |   Difficulty %s   |   %d weeks of science" % (
                m["budget"], "*" * m["stars"] + "-" * (4 - m["stars"]), m["ops"]), fg=WARN, bg=PANEL, font=FB).pack(pady=(4, 0))
            tk.Label(card, text=m["desc"], fg=FG, bg=PANEL, font=F9, justify="left").pack()
            tk.Button(card, text="SELECT MISSION", font=FB, bg=GOOD, fg="black",
                      command=lambda mid=mid: self.show_design(mid)).pack(pady=4)
        tk.Label(f, text="Tip: launch, cruise, orbit insertion and 26 weeks of operations are all simulated - "
                         "a design that looks fine on paper can still fail in flight.", fg="#8fa3d9", bg=BG, font=F9).pack()

    # ==================================================================== DESIGN
    def show_design(self, mid):
        f = self.clear()
        self.design = Design(mid)
        d, m = self.design, self.design.m
        hdr = tk.Frame(f, bg=BG)
        hdr.pack(fill="x", padx=10, pady=(6, 0))
        tk.Label(hdr, text="%s  -  %s   |   budget $%.0fM   |   science goal %d pts" % (m["title"], m["sub"], m["budget"], m["goal"]),
                 fg=ACC, bg=BG, font=("Helvetica", 13, "bold")).pack(side="left")
        tk.Button(hdr, text="< Change mission", command=self.show_select).pack(side="right")
        body = tk.Frame(f, bg=BG)
        body.pack(fill="both", expand=True, padx=8, pady=4)
        c1, c2, c3 = tk.Frame(body, bg=BG), tk.Frame(body, bg=BG), tk.Frame(body, bg=BG)
        c1.grid(row=0, column=0, sticky="n")
        c2.grid(row=0, column=1, sticky="n", padx=6)
        c3.grid(row=0, column=2, sticky="n")
        self.v = dict(launcher=tk.IntVar(value=d.launcher), solar=tk.DoubleVar(value=d.solar), rtg=tk.IntVar(value=d.rtg),
                      battery=tk.DoubleVar(value=d.battery), ptype=tk.StringVar(value=d.prop_type),
                      prop=tk.DoubleVar(value=d.prop), dish=tk.DoubleVar(value=d.dish), tx=tk.DoubleVar(value=d.tx),
                      rec=tk.IntVar(value=d.rec), harden=tk.IntVar(value=d.harden), redund=tk.IntVar(value=d.redund))
        self.iv = {k: tk.BooleanVar(value=False) for k in INSTR_ORDER}

        def box(parent, title):
            b = tk.LabelFrame(parent, text=" %s " % title, fg=ACC, bg=PANEL, font=FB, padx=4, pady=2)
            b.pack(fill="x", pady=3)
            return b

        # A. launcher
        b = box(c1, "1  LAUNCH VEHICLE")
        g = tk.Frame(b, bg=PANEL)
        g.pack()
        for i, L in enumerate(LAUNCHERS):
            tk.Radiobutton(g, text="%s\n%d kg LEO | $%dM | %d%% reliable" % (L["name"], L["cap"], L["cost"], round(L["rel"] * 100)),
                           value=i, variable=self.v["launcher"], indicatoron=0, width=22, font=("Helvetica", 8),
                           bg="#1c2547", fg=FG, selectcolor="#2f5bd0", command=self.on_change).grid(row=i // 2, column=i % 2, padx=2, pady=2)
        self.cap_lbl = tk.Label(b, text="", fg=WARN, bg=PANEL, font=F9)
        self.cap_lbl.pack()
        # B. power
        b = box(c1, "2  POWER")
        self.scale_row(b, "Solar area (m2)", self.v["solar"], 0, 40, 0.5)
        self.scale_row(b, "RTGs (110 W each)", self.v["rtg"], 0, 3, 1)
        self.scale_row(b, "Battery (Wh)", self.v["battery"], 0, 3000, 50)
        # C. propulsion
        b = box(c1, "3  PROPULSION")
        g = tk.Frame(b, bg=PANEL)
        g.pack()
        for k, P in PROP.items():
            tk.Radiobutton(g, text="%s\nIsp %d s" % (P["name"], P["isp"]), value=k, variable=self.v["ptype"], indicatoron=0,
                           width=15, font=("Helvetica", 8), bg="#1c2547", fg=FG, selectcolor="#2f5bd0",
                           command=self.on_change).pack(side="left", padx=2, pady=2)
        self.scale_row(b, "Propellant (kg)", self.v["prop"], 0, 4000, 5)
        tk.Button(b, text="Auto-size propellant for required delta-v (+12%)", font=F9, command=self.on_auto).pack(pady=2)
        # D. comms
        b = box(c2, "4  COMMUNICATIONS & DATA")
        self.scale_row(b, "Dish diameter (m)", self.v["dish"], 0.3, 4.5, 0.1)
        self.scale_row(b, "Transmitter (W)", self.v["tx"], 5, 150, 5)
        g = tk.Frame(b, bg=PANEL)
        g.pack()
        tk.Label(g, text="Recorder:", fg=FG, bg=PANEL, font=F9).pack(side="left")
        for i, R in enumerate(RECORDERS):
            tk.Radiobutton(g, text="%d Gb" % R["gb"], value=i, variable=self.v["rec"], indicatoron=0, width=7, font=F9,
                           bg="#1c2547", fg=FG, selectcolor="#2f5bd0", command=self.on_change).pack(side="left", padx=2, pady=2)
        # E. payload
        b = box(c2, "5  SCIENCE PAYLOAD")
        for k in INSTR_ORDER:
            i = INSTR[k]
            tk.Checkbutton(b, text="%-22s %3dkg %3dW $%2dM  sci %.0f" % (i["name"], i["mass"], i["power"], i["cost"], i["sci"] * i["rel"][mid]),
                           variable=self.iv[k], anchor="w", fg=i["color"], bg=PANEL, selectcolor="#0b0f20",
                           activebackground=PANEL, activeforeground=FG, font=("Courier", 8), command=self.on_change).pack(fill="x")
        tk.Label(b, text="(sci = points per week for THIS mission)", fg="#8fa3d9", bg=PANEL, font=("Helvetica", 8)).pack()
        # F. bus
        b = box(c2, "6  SURVIVABILITY")
        for key, lab, arr in (("harden", "Radiation hardening", HARDEN), ("redund", "Redundancy", REDUND)):
            g = tk.Frame(b, bg=PANEL)
            g.pack(fill="x")
            tk.Label(g, text=lab, width=17, anchor="w", fg=FG, bg=PANEL, font=F9).pack(side="left")
            for i, a in enumerate(arr):
                tk.Radiobutton(g, text=a["name"], value=i, variable=self.v[key], indicatoron=0, width=11, font=("Helvetica", 8),
                               bg="#1c2547", fg=FG, selectcolor="#2f5bd0", command=self.on_change).pack(side="left", padx=1, pady=1)
        # right column
        self.craft = tk.Canvas(c3, width=640, height=250, bg="black", highlightthickness=1, highlightbackground=ACC)
        self.craft.pack()
        self.gauges = tk.Canvas(c3, width=640, height=205, bg=PANEL, highlightthickness=0)
        self.gauges.pack(pady=4)
        self.review = tk.Text(c3, width=84, height=11, bg="#0d1226", fg=FG, font=("Courier", 8), wrap="word",
                              state="disabled", highlightthickness=0)
        self.review.pack()
        for tag, col in (("ok", GOOD), ("warn", WARN), ("fail", BAD), ("head", ACC)):
            self.review.tag_config(tag, foreground=col)
        bar = tk.Frame(c3, bg=BG)
        bar.pack(fill="x", pady=5)
        self.launch_btn = tk.Button(bar, text="FLIGHT READINESS  >>  LAUNCH", font=("Helvetica", 13, "bold"), bg=GOOD, fg="black",
                                    command=self.on_launch_click)
        self.launch_btn.pack(side="right")
        self.cost_lbl = tk.Label(bar, text="", fg=FG, bg=BG, font=FB)
        self.cost_lbl.pack(side="left")
        self.ready = True
        self.on_change()

    def scale_row(self, parent, text, var, lo, hi, res):
        r = tk.Frame(parent, bg=PANEL)
        r.pack(fill="x")
        tk.Label(r, text=text, width=16, anchor="w", bg=PANEL, fg=FG, font=F9).pack(side="left")
        tk.Scale(r, from_=lo, to=hi, resolution=res, orient="horizontal", variable=var, length=180, showvalue=True,
                 bg=PANEL, fg=FG, troughcolor="#0b0f20", highlightthickness=0, width=12,
                 command=lambda v: self.on_change()).pack(side="left")

    def sync(self):
        d, v = self.design, self.v
        d.launcher, d.solar, d.rtg, d.battery = v["launcher"].get(), float(v["solar"].get()), v["rtg"].get(), float(v["battery"].get())
        d.prop_type, d.prop = v["ptype"].get(), float(v["prop"].get())
        d.dish, d.tx, d.rec = float(v["dish"].get()), float(v["tx"].get()), v["rec"].get()
        d.harden, d.redund = v["harden"].get(), v["redund"].get()
        d.inst = {k for k in INSTR_ORDER if self.iv[k].get()}

    def on_auto(self):
        self.sync()
        self.design.auto_prop()
        self.v["prop"].set(self.design.prop)
        self.on_change()

    def on_change(self):
        if not self.ready:
            return
        self.sync()
        c = self.design.compute()
        self.comp = c
        self.cap_lbl.config(text="Capacity to this destination: %.0f kg" % c["cap"])
        self.draw_design_craft(c)
        self.draw_design_gauges(c)
        self.draw_review(c)
        self.cost_lbl.config(text="Total cost $%.0fM of $%.0fM" % (c["total"], self.design.m["budget"]),
                             fg=BAD if c["reserve"] < 0 else FG)
        self.launch_btn.config(state="disabled" if c["blockers"] else "normal")

    def draw_design_craft(self, c):
        cv, d = self.craft, self.design
        cv.delete("all")
        self.starfield(cv)
        draw_spacecraft(cv, 320, 120, d, c, 1.0)
        cv.create_text(10, 8, anchor="nw", fill="white", font=FB, text="YOUR SPACECRAFT")
        cv.create_text(10, 26, anchor="nw", fill="#9fb4ff", font=F9,
                       text="dry %.0f kg | wet %.0f kg | %d instruments" % (c["dry"], c["wet"], len(d.inst)))
        # mass breakdown bars
        x = 10
        tot = max(1.0, c["dry"])
        cols = ["#7fd0ff", "#ffe066", "#7dffb0", "#c78bff", "#ff9a5a", "#f78fb3", "#8c8f98", "#e0e0e8", "#a8862a"]
        for (name, val), col in zip(c["parts"], cols):
            w = 620 * val / tot
            cv.create_rectangle(x, 226, x + w, 240, fill=col, outline="")
            x += w
        cv.create_text(10, 214, anchor="w", fill="#9fb4ff", font=("Helvetica", 8),
                       text="Dry-mass breakdown: " + ", ".join("%s %.0f" % (n[:10], v) for n, v in c["parts"] if v > 0.5))

    def bar(self, cv, x, y, w, label, frac, col, txt, mark=None):
        cv.create_text(x, y, anchor="w", text=label, fill=FG, font=("Helvetica", 8, "bold"))
        cv.create_text(x + w, y, anchor="e", text=txt, fill="#c8d2f5", font=("Helvetica", 8))
        cv.create_rectangle(x, y + 8, x + w, y + 22, fill="#0b0f20", outline="#33406b")
        cv.create_rectangle(x, y + 8, x + w * max(0.0, min(1.0, frac)), y + 22, fill=col, outline="")
        if mark is not None:
            cv.create_line(x + w * mark, y + 5, x + w * mark, y + 25, fill="white")

    def draw_design_gauges(self, c):
        cv, m = self.gauges, self.design.m
        cv.delete("all")
        gc = lambda ok, warn: GOOD if ok else WARN if warn else BAD
        rows = [
            ("MASS", c["wet"] / c["cap"], gc(c["wet"] <= 0.92 * c["cap"], c["wet"] <= c["cap"]), "%.0f / %.0f kg" % (c["wet"], c["cap"]), None),
            ("COST", c["total"] / m["budget"], gc(c["total"] <= 0.95 * m["budget"], c["total"] <= m["budget"]),
             "$%.0fM / $%.0fM" % (c["total"], m["budget"]), None),
            ("DELTA-V", c["dv"] / (c["dv_req"] * 1.5), gc(c["margin"] >= 1.1, c["margin"] >= 1.0),
             "%.2f km/s (need %.2f)" % (c["dv"], c["dv_req"]), 1 / 1.5),
            ("POWER (avg gen vs load)", c["gen"] / c["load"], gc(c["gen"] >= 1.05 * c["load"], c["gen"] >= c["base"] + 0.5 * c["i_pow"]),
             "%.0f / %.0f W" % (c["gen"], c["load"]), None),
            ("DOWNLINK", c["down"] / c["data"] if c["data"] > 0 else 1.0, gc(c["down"] >= c["data"], c["down"] >= 0.5 * c["data"]),
             "%.0f / %.0f Gb/wk" % (c["down"], c["data"]), None),
            ("SCIENCE vs GOAL", c["sci_pot"] / (1.5 * m["goal"]), gc(c["sci_pot"] >= 1.1 * m["goal"], c["sci_pot"] >= 0.7 * m["goal"]),
             "%.0f / %d pts" % (c["sci_pot"], m["goal"]), 1 / 1.5),
        ]
        for i, (lab, fr, col, txt, mk) in enumerate(rows):
            self.bar(cv, 12 + (i % 2) * 320, 12 + (i // 2) * 66, 296, lab, fr, col, txt, mk)
        cv.create_text(12, 200, anchor="w", fill="#8fa3d9", font=("Helvetica", 8),
                       text="Downlink rate %.0f kbps | arrival after %.0f wks | launch reliability %d%%" % (
                           c["rate"], c["arrival"], round(LAUNCHERS[self.design.launcher]["rel"] * 100)))

    def draw_review(self, c):
        t = self.review
        t.config(state="normal")
        t.delete("1.0", "end")
        t.insert("end", "FLIGHT READINESS REVIEW\n", "head")
        sym = {"ok": "[ OK ]", "warn": "[WARN]", "fail": "[FAIL]"}
        for name, st, msg in c["checks"]:
            t.insert("end", "%s %-11s %s\n" % (sym[st], name, msg), st)
        t.config(state="disabled")

    def on_launch_click(self):
        self.sync()
        c = self.design.compute()
        if c["blockers"]:
            return
        soft = [n for n, s, _ in c["checks"] if s == "fail"]
        if soft:
            if not messagebox.askyesno("Readiness review",
                                       "These items are FAILING: %s.\n\nLaunch anyway?" % ", ".join(soft)):
                return
        self.show_flight()

    # ==================================================================== FLIGHT
    def show_flight(self):
        f = self.clear()
        self.flight = Flight(self.design)
        fl, m = self.flight, self.design.m
        left, right = tk.Frame(f, bg=BG), tk.Frame(f, bg=BG)
        left.grid(row=0, column=0, padx=8, pady=6, sticky="n")
        right.grid(row=0, column=1, pady=6, sticky="n")
        self.canvas = tk.Canvas(left, width=self.SW, height=self.SH, bg="black", highlightthickness=1, highlightbackground=ACC)
        self.canvas.pack()
        self.logbox = tk.Text(left, width=100, height=14, bg="#0d1226", fg=FG, font=("Courier", 9), wrap="word",
                              state="disabled", highlightthickness=0)
        self.logbox.pack(pady=6)
        for tag, col in (("good", GOOD), ("warn", WARN), ("bad", BAD), ("info", "#8fa3d9"), ("head", ACC)):
            self.logbox.tag_config(tag, foreground=col)
        self.meter = tk.Canvas(right, width=470, height=330, bg=PANEL, highlightthickness=0)
        self.meter.pack()
        self.ctrl = tk.Frame(right, bg=BG)
        self.ctrl.pack(fill="x", pady=6)
        self.next_btn = tk.Button(self.ctrl, text="LAUNCH  >>", font=("Helvetica", 15, "bold"), bg=GOOD, fg="black",
                                  command=self.advance_stage)
        self.next_btn.pack(fill="x")
        self.ops_frame = tk.Frame(right, bg=BG)
        self.ivars = {k: tk.BooleanVar(value=True) for k in fl.ih}
        pf = tk.LabelFrame(self.ops_frame, text=" INSTRUMENTS (tick = ON) ", fg=ACC, bg=PANEL, font=FB)
        pf.pack(fill="x")
        for k in INSTR_ORDER:
            if k in self.ivars:
                tk.Checkbutton(pf, text="%s  (%d W)" % (INSTR[k]["name"], INSTR[k]["power"]), variable=self.ivars[k],
                               anchor="w", fg=INSTR[k]["color"], bg=PANEL, selectcolor="#0b0f20", activebackground=PANEL,
                               font=F9, command=self.refresh_meter).pack(fill="x")
        self.safe_var, self.diag_var = tk.BooleanVar(value=False), tk.BooleanVar(value=False)
        af = tk.LabelFrame(self.ops_frame, text=" THIS WEEK'S ACTIONS ", fg=ACC, bg=PANEL, font=FB)
        af.pack(fill="x", pady=4)
        tk.Checkbutton(af, text="SAFE MODE (instruments off - shields from solar storms)", variable=self.safe_var, anchor="w",
                       fg=WARN, bg=PANEL, selectcolor="#0b0f20", activebackground=PANEL, font=F9,
                       command=self.refresh_meter).pack(fill="x")
        tk.Checkbutton(af, text="Run diagnostics (-$0.5M, prevents software glitches 3 wks)", variable=self.diag_var, anchor="w",
                       fg=FG, bg=PANEL, selectcolor="#0b0f20", activebackground=PANEL, font=F9).pack(fill="x")
        bf = tk.Frame(self.ops_frame, bg=BG)
        bf.pack(fill="x")
        tk.Button(bf, text="ADVANCE 1 WEEK", font=FB, bg=ACC, fg="black", command=self.do_week).pack(side="left", expand=True, fill="x", padx=2)
        tk.Button(bf, text="AUTO x4 (stops on trouble)", font=FB, bg="#8fa3d9", fg="black", command=self.do_auto).pack(side="left", expand=True, fill="x", padx=2)
        self.stage = "pad"
        self.log("MISSION %s  -  T-0. Vehicle: %s, spacecraft %.0f kg." % (
            m["title"], LAUNCHERS[self.design.launcher]["name"], fl.c["wet"]), "head")
        self.draw_pad()
        self.refresh_meter()

    def log(self, msg, tag="info"):
        self.logbox.config(state="normal")
        self.logbox.insert("end", msg + "\n", tag)
        self.logbox.see("end")
        self.logbox.config(state="disabled")

    def run_anim(self, fn, frames, done, delay=35):
        st = dict(i=0)

        def tick():
            if not self.flight:
                return
            if st["i"] >= frames:
                done()
                return
            fn(st["i"], frames)
            st["i"] += 1
            self.later(delay, tick)
        tick()

    # ---- stage machine ----
    def advance_stage(self):
        fl = self.flight
        if self.stage == "pad":
            self.next_btn.config(state="disabled")
            ok = fl.launch()
            self.log("Ignition... liftoff!", "info")
            self.run_anim(lambda i, n: self.launch_frame(i, n, ok), 80, lambda: self.after_launch(ok))
        elif self.stage == "cruise":
            self.next_btn.config(state="disabled")
            for msg, tag in fl.cruise():
                self.log(msg, tag)
            self.run_anim(self.cruise_frame, 70, self.after_cruise)
        elif self.stage == "insertion":
            self.next_btn.config(state="disabled")
            ok, msgs = fl.insertion()
            for msg, tag in msgs:
                self.log(msg, tag)
            self.run_anim(lambda i, n: self.insert_frame(i, n, ok), 70, lambda: self.after_insertion(ok))

    def after_launch(self, ok):
        if not ok:
            self.log("LAUNCH FAILURE. The vehicle was lost.", "bad")
            self.finish()
            return
        self.log("Successful launch. Spacecraft separated and solar arrays deployed.", "good")
        self.stage = "cruise"
        self.next_btn.config(state="normal", text="CRUISE TO %s  >>" % self.design.m["body"].upper())
        self.refresh_meter()

    def after_cruise(self):
        self.stage = "insertion"
        self.next_btn.config(state="normal", text="FIRE ORBIT-INSERTION BURN  >>")
        self.refresh_meter()

    def after_insertion(self, ok):
        if not ok:
            self.finish()
            return
        self.stage = "ops"
        self.next_btn.pack_forget()
        self.ops_frame.pack(fill="x")
        self.log("=== SCIENCE OPERATIONS BEGIN: %d weeks ===" % self.design.m["ops"], "head")
        self.log("Tip: keep instrument power within the generated power; watch the data pool and the storm warnings.", "info")
        self.draw_ops_static()
        self.refresh_meter()
        self.tick_ops()

    def do_week(self, safe=None, diag=None):
        fl = self.flight
        if self.stage != "ops" or fl.ended:
            return []
        on = {k for k, v in self.ivars.items() if v.get()}
        safe = self.safe_var.get() if safe is None else safe
        diag = self.diag_var.get() if diag is None else diag
        out = fl.step(on, safe, diag)
        self.safe_var.set(False)
        self.diag_var.set(False)
        self.log("--- Week %d/%d: %.0f pts returned so far ---" % (fl.week, self.design.m["ops"], fl.returned), "head")
        for msg, tag in out:
            self.log(msg, tag)
        self.refresh_meter()
        if fl.ended:
            self.finish()
        return out

    def do_auto(self):
        first = True
        for _ in range(4):
            out = self.do_week(None if first else False, None if first else False)
            first = False
            if self.flight.ended or any(t in ("bad", "warn") for _, t in out):
                break

    def finish(self):
        self.stage = "done"
        self.later(1200, self.show_report)

    # ---- meters ----
    def refresh_meter(self):
        if not self.flight:
            return
        cv, fl, m = self.meter, self.flight, self.design.m
        cv.delete("all")
        pc = fl.power_calc({k for k, v in self.ivars.items() if v.get()} if self.stage == "ops" else set(fl.ih),
                           self.safe_var.get() if self.stage == "ops" else False)
        g = lambda x: GOOD if x > 0.5 else WARN if x > 0.25 else BAD
        sci = fl.returned / m["goal"]
        avg_ih = sum(fl.ih.values()) / max(1, len(fl.ih))
        rows = [
            ("SCIENCE RETURNED", sci, ACC, "%.0f / %d pts (%d%%)" % (fl.returned, m["goal"], round(sci * 100)), 0.7),
            ("POWER (generated vs load)", pc["gen"] / pc["load"] if pc["load"] else 1.0,
             GOOD if pc["gen"] >= pc["load"] else WARN if pc["duty"] > 0.6 else BAD, "%.0f / %.0f W" % (pc["gen"], pc["load"]), None),
            ("ONBOARD DATA POOL", fl.pool_data / max(1, RECORDERS[self.design.rec]["gb"]),
             GOOD if fl.pool_data < 0.6 * RECORDERS[self.design.rec]["gb"] else WARN if fl.pool_data < 0.9 * RECORDERS[self.design.rec]["gb"] else BAD,
             "%.0f / %d Gb (lost %.0f)" % (fl.pool_data, RECORDERS[self.design.rec]["gb"], fl.lost), None),
            ("PROPELLANT", fl.prop_left / max(1.0, self.design.prop), None, "%.0f / %.0f kg" % (fl.prop_left, self.design.prop), None),
            ("SOLAR ARRAY HEALTH", fl.solar_health, None, "%d%%" % round(fl.solar_health * 100), None),
            ("COMMS HEALTH", fl.comm_health, None, "%d%%" % round(fl.comm_health * 100), None),
            ("INSTRUMENT HEALTH (avg)", avg_ih, None, "%d%%" % round(avg_ih * 100), None),
            ("CONTINGENCY RESERVE", fl.reserve / m["budget"], None, "$%.1fM of $%.0fM budget" % (fl.reserve, m["budget"]), None),
        ]
        for i, (lab, fr, col, txt, mk) in enumerate(rows):
            self.bar(cv, 12, 8 + i * 40, 446, lab, fr, col or g(fr), txt, mk)
        if self.stage == "ops":
            cv.create_text(12, 322, anchor="w", font=("Helvetica", 8), fill=WARN if fl.storm_warned else "#8fa3d9",
                           text="STORM WARNING: tick SAFE MODE this week!" if fl.storm_warned else
                           "Week %d/%d | downlink cap %.0f Gb/wk | duty %d%%" % (fl.week, m["ops"], fl.downlink_capacity(), round(pc["duty"] * 100)))

    # ---- scenes ----
    def body_r(self):
        return {"Earth": 105, "Moon": 80, "Mars": 90, "Jupiter": 125}[self.design.m["body"]]

    def draw_pad(self):
        self.launch_frame(0, 80, True)

    def launch_frame(self, i, n, ok):
        c = self.canvas
        c.delete("all")
        t = i / float(n)
        c.create_rectangle(0, 0, self.SW, self.SH, fill=mix("#5aa7ff", "#000010", min(1.0, t * 1.5)), outline="")
        if t > 0.25:
            for x, y, s in self.stars:
                c.create_oval(x, y, x + s, y + s, fill="white", outline="")
        rise = 230 * (min(t, 0.85) / 0.85) ** 1.7
        gy = 350 + rise * 3
        c.create_rectangle(0, gy, self.SW, self.SH + 900, fill="#2e7d32", outline="")
        c.create_rectangle(300, gy - 6, 420, gy, fill="#777", outline="")
        c.create_rectangle(430, gy - 120, 442, gy, fill="#a33", outline="")
        tier = self.design.launcher
        rw, rh = 16 + tier * 6, 80 + tier * 26
        rx, base = 360, 350 - rise
        if not ok and t >= 0.55:
            tt = (t - 0.55) / 0.45
            for k, col in enumerate(("#ff3b1f", "#ff9a1f", "#ffe066")):
                r = (20 + 90 * tt) * (1 - k * 0.28)
                c.create_oval(rx - r, base - rh / 2 - r, rx + r, base - rh / 2 + r, fill=col, outline="")
            c.create_text(rx, 60, text="ANOMALY - VEHICLE LOST", fill=BAD, font=("Helvetica", 20, "bold"))
        elif t < 0.85:
            c.create_rectangle(rx - rw / 2, base - rh, rx + rw / 2, base, fill="#e9e9ee", outline="#555")
            c.create_polygon(rx - rw / 2, base - rh, rx + rw / 2, base - rh, rx, base - rh - rw * 1.3, fill="#c33", outline="#555")
            c.create_polygon(rx - rw / 2, base - 5, rx - rw, base + 12, rx - rw / 2, base - 25, fill="#777", outline="")
            c.create_polygon(rx + rw / 2, base - 5, rx + rw, base + 12, rx + rw / 2, base - 25, fill="#777", outline="")
            if t > 0.02:
                fl = 25 + 30 * ((i % 3) / 2.0) + rise * 0.05
                c.create_polygon(rx - rw / 3, base, rx + rw / 3, base, rx, base + fl, fill="#ffb02e", outline="")
                c.create_polygon(rx - rw / 6, base, rx + rw / 6, base, rx, base + fl * 0.6, fill="#fff3a0", outline="")
                if t < 0.2:
                    for k in range(6):
                        c.create_oval(rx - 30 - k * 8, gy - 12 - k * 4, rx + 30 + k * 8, gy + 4, outline="#ddd")
        else:
            sx = 360 + (t - 0.85) * 900
            c.create_text(360, 30, text="STAGE SEPARATION - SPACECRAFT DEPLOYED", fill=GOOD, font=FB)
            draw_spacecraft(c, sx, 120, self.design, self.flight.c, 0.5)
        c.create_text(12, 12, anchor="nw", fill="white", font=("Helvetica", 12, "bold"),
                      text="T+%02d s   ALT %d km" % (int(t * 160), int(t * t * 200)))

    def system_geometry(self):
        return self.design.m["body"] in ("Mars", "Jupiter")

    def cruise_frame(self, i, n):
        c, m = self.canvas, self.design.m
        c.delete("all")
        self.starfield(c)
        p = i / float(n)
        if self.system_geometry():
            cx, cy, r1 = 360, 215, 80
            r2 = 150 if m["body"] == "Mars" else 185
            c.create_oval(cx - 18, cy - 18, cx + 18, cy + 18, fill="#ffd54a", outline="#fff3b0", width=3)
            for r in (r1, r2):
                c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#33406b")
            a, e = (r1 + r2) / 2.0, (r2 - r1) / float(r1 + r2)
            pts = []
            for k in range(41):
                th = math.pi * k / 40.0
                rr = a * (1 - e * e) / (1 + e * math.cos(th))
                pts += [cx + rr * math.cos(th), cy - rr * math.sin(th)]
            c.create_line(pts, fill="#5ad1ff", dash=(4, 3))
            c.create_oval(cx + r1 - 7, cy - 7, cx + r1 + 7, cy + 7, fill="#2a6fdb", outline="")
            c.create_text(cx + r1 + 10, cy + 16, text="Earth", fill="#9fb4ff", font=F9)
            tr = 9 if m["body"] == "Mars" else 15
            c.create_oval(cx - r2 - tr, cy - tr, cx - r2 + tr, cy + tr, fill="#c1633a" if m["body"] == "Mars" else "#d9b38c", outline="")
            c.create_text(cx - r2, cy + tr + 10, text=m["body"], fill="#9fb4ff", font=F9)
            th = math.pi * p
            rr = a * (1 - e * e) / (1 + e * math.cos(th))
            sx, sy = cx + rr * math.cos(th), cy - rr * math.sin(th)
        else:
            ex, ey = 150, 215
            c.create_oval(ex - 55, ey - 55, ex + 55, ey + 55, fill="#1f5fbf", outline="#8fc4ff")
            c.create_oval(ex - 30, ey - 30, ex - 5, ey - 10, fill="#3a9d4f", outline="")
            if m["body"] == "Moon":
                mx = 600
                c.create_oval(mx - 22, ey - 22, mx + 22, ey + 22, fill="#b9b9c0", outline="#e5e5ea")
                c.create_text(mx, ey + 36, text="Moon", fill="#9fb4ff", font=F9)
                t2 = p
                sx = 215 + (mx - 40 - 215) * t2
                sy = ey - 150 * math.sin(math.pi * t2) * (1 - t2 * 0.3)
                pts = []
                for k in range(31):
                    tt = k / 30.0
                    pts += [215 + (mx - 40 - 215) * tt, ey - 150 * math.sin(math.pi * tt) * (1 - tt * 0.3)]
                c.create_line(pts, fill="#5ad1ff", dash=(4, 3))
            else:
                ang = p * 4 * math.pi
                rr = 62 + 22 * p
                sx, sy = ex + rr * math.cos(ang), ey + rr * math.sin(ang) * 0.9
                c.create_oval(ex - 84, ey - 76, ex + 84, ey + 76, outline="#33406b", dash=(3, 3))
        draw_spacecraft(c, sx, sy, self.design, self.flight.c, 0.3)
        c.create_text(12, 12, anchor="nw", fill="white", font=("Helvetica", 13, "bold"),
                      text="CRUISE  -  %d%% of the way (%.0f weeks total)" % (int(p * 100), self.flight.c["arrival"]))

    def insert_frame(self, i, n, ok):
        c = self.canvas
        c.delete("all")
        self.starfield(c)
        p = i / float(n)
        cx, cy, r = 360, 215, self.body_r()
        draw_planet(c, cx, cy, r, self.design.m["body"], "static")
        orb = r + 60
        if p < 0.5:
            q = p / 0.5
            sx, sy = 730 - 300 * q, 40 + 140 * q
        elif ok:
            q = (p - 0.5) / 0.5
            a0 = math.atan2(180 - cy, 430 - cx)
            a = a0 + q * 2 * math.pi
            rr = math.hypot(430 - cx, 180 - cy) * (1 - q) + orb * q
            sx, sy = cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.55
        else:
            q = (p - 0.5) / 0.5
            sx, sy = 430 - 420 * q, 180 + 90 * q
        if ok:
            c.create_oval(cx - orb, cy - orb * 0.55, cx + orb, cy + orb * 0.55, outline="#5ad1ff", dash=(3, 3))
        if 0.35 < p < 0.62:
            c.create_polygon(sx, sy, sx + 40, sy - 8, sx + 28, sy + 2, sx + 40, sy + 10, fill="#ffb02e", outline="")
        draw_spacecraft(c, sx, sy, self.design, self.flight.c, 0.3)
        txt = "ORBIT INSERTION BURN" + ("" if p < 0.5 else ("  -  CAPTURED" if ok else "  -  MISSED"))
        c.create_text(12, 12, anchor="nw", fill=GOOD if (ok and p > 0.5) else BAD if (not ok and p > 0.5) else "white",
                      font=("Helvetica", 14, "bold"), text=txt)

    def draw_ops_static(self):
        c = self.canvas
        c.delete("all")
        self.starfield(c)
        r = self.body_r()
        cx, cy = 360, 235
        draw_planet(c, cx, cy, r, self.design.m["body"], "static")
        orb = r + 62
        c.create_oval(cx - orb, cy - orb * 0.45, cx + orb, cy + orb * 0.45, outline="#33406b", dash=(3, 3), tags="static")
        c.create_oval(14, 190, 60, 236, fill="#ffd54a", outline="#fff3b0", width=3, tags="static")
        c.create_text(37, 250, text="Sun", fill="#ffe680", font=F9, tags="static")
        c.create_rectangle(640, 60, 668, 66, fill="#888", outline="", tags="static")
        c.create_oval(636, 40, 672, 62, fill="#e8e8ee", outline="#666", tags="static")
        c.create_text(654, 82, text="Ground station", fill="#9fb4ff", font=F9, tags="static")

    def tick_ops(self):
        if self.stage != "ops":
            return
        self.ang += 0.05
        self.draw_ops_dyn()
        self.later(80, self.tick_ops)

    def draw_ops_dyn(self):
        c, fl = self.canvas, self.flight
        c.delete("dyn")
        r = self.body_r()
        cx, cy = 360, 235
        orb = r + 62
        sx, sy = cx + orb * math.cos(self.ang), cy + orb * 0.45 * math.sin(self.ang)
        behind = math.sin(self.ang) < 0 and abs(sx - cx) < r
        if not behind:
            if fl.last["dl"] > 0:
                c.create_line(sx, sy, 654, 62, fill="#5ad1ff", dash=(4, 3), width=2, tags="dyn")
            draw_spacecraft(c, sx, sy, self.design, fl.c, 0.28, tag="dyn", dim=fl.last["safe"])
        m = self.design.m
        c.create_text(12, 10, anchor="nw", fill="white", font=("Helvetica", 14, "bold"), tags="dyn",
                      text="WEEK %d / %d   -   %s" % (min(fl.week + (0 if fl.ended else 1), m["ops"]), m["ops"], m["title"]))
        status, col = ("SAFE MODE", WARN) if fl.last["safe"] else ("NOMINAL", GOOD)
        c.create_text(12, 34, anchor="nw", fill=col, font=FB, text="Status: " + status, tags="dyn")
        c.create_text(12, 52, anchor="nw", fill="#9fb4ff", font=F9, tags="dyn",
                      text="Last downlink: %.0f Gb   |   generated %.0f W" % (fl.last["dl"], fl.last["gen"]))
        if fl.storm_warned:
            c.create_rectangle(150, 380, 570, 410, fill="#7a0d0d", outline=BAD, width=2, tags="dyn")
            c.create_text(360, 395, text="!! SOLAR STORM INBOUND - USE SAFE MODE !!", fill="white", font=FB, tags="dyn")

    # ==================================================================== REPORT
    def show_report(self):
        fl, m = self.flight, self.design.m
        title, score, frac = fl.result()
        ok = title not in ("MISSION LOSS",)
        f = self.clear()
        col = GOOD if ok and frac >= 0.7 else WARN if ok else BAD
        tk.Label(f, text=title, font=("Helvetica", 30, "bold"), fg=col, bg=BG).pack(pady=(14, 0))
        tk.Label(f, text=fl.reason, fg=FG, bg=BG, font=("Helvetica", 12), wraplength=1000).pack()
        tk.Label(f, text="Science returned: %.0f of %d goal points (%d%%)     Score: %d     Weeks operated: %d/%d" % (
            fl.returned, m["goal"], round(frac * 100), score, fl.week, m["ops"]), fg=ACC, bg=BG, font=("Helvetica", 12, "bold")).pack(pady=6)
        mid = tk.Frame(f, bg=BG)
        mid.pack(pady=4)
        cv = tk.Canvas(mid, width=560, height=230, bg=PANEL, highlightthickness=0)
        cv.grid(row=0, column=0, padx=10)
        cv.create_text(10, 10, anchor="nw", text="Cumulative science returned (weeks)", fill=FG, font=FB)
        x0, y0, w, h = 40, 200, 500, 150
        cv.create_line(x0, y0, x0 + w, y0, fill="#888")
        cv.create_line(x0, y0, x0, y0 - h, fill="#888")
        top = max(m["goal"] * 1.2, max(fl.hist) if fl.hist else 1)
        gy = y0 - h * m["goal"] / top
        cv.create_line(x0, gy, x0 + w, gy, fill=GOOD, dash=(4, 3))
        cv.create_text(x0 + w, gy - 8, anchor="e", text="goal", fill=GOOD, font=F9)
        if len(fl.hist) > 1:
            pts = []
            for k, v in enumerate(fl.hist):
                pts += [x0 + w * (k + 1) / float(m["ops"]), y0 - h * v / top]
            cv.create_line(pts, fill=ACC, width=2)
        lessons = self.lessons()
        tk.Label(mid, text="ENGINEER'S REVIEW\n\n" + "\n\n".join("- " + s for s in lessons), justify="left", wraplength=560,
                 fg=FG, bg=PANEL, padx=12, pady=10, font=F10).grid(row=0, column=1, padx=10)
        cost_txt = "Total cost $%.0fM of $%.0fM budget (reserve left $%.1fM)   |   Launch %s   |   Mass %.0f kg" % (
            m["budget"] - fl.reserve, m["budget"], fl.reserve,
            LAUNCHERS[self.design.launcher]["name"], fl.c["wet"])
        tk.Label(f, text=cost_txt, fg="#8fa3d9", bg=BG, font=F9).pack(pady=4)
        bf = tk.Frame(f, bg=BG)
        bf.pack(pady=8)
        tk.Button(bf, text="REDESIGN (same mission)", font=("Helvetica", 12, "bold"), bg=GOOD, fg="black",
                  command=lambda: self.show_design(self.design.mid)).pack(side="left", padx=8)
        tk.Button(bf, text="NEW MISSION", font=("Helvetica", 12, "bold"), bg=ACC, fg="black",
                  command=self.show_select).pack(side="left", padx=8)
        tk.Button(bf, text="QUIT", font=("Helvetica", 12), command=self.root.destroy).pack(side="left", padx=8)

    def lessons(self):
        fl, m, d, c = self.flight, self.design.m, self.design, self.flight.c
        out = []
        if fl.reason.startswith("The launch vehicle"):
            out.append("Launch reliability (%d%%) is a real risk. A pricier, more reliable rocket is insurance for everything "
                       "you spent on the spacecraft." % round(LAUNCHERS[d.launcher]["rel"] * 100))
        if "Propellant ran out" in fl.reason or c["margin"] < 1.0:
            out.append("Delta-v: the rocket equation needs %.2f km/s but the design offered %.2f. More propellant helps only "
                       "with a higher-Isp engine or a lighter spacecraft." % (c["dv_req"], c["dv"]))
        if "engine failed" in fl.reason:
            out.append("Engine reliability: complex bipropellant engines are more efficient but fail more often than "
                       "simple monopropellant ones. Margin in delta-v cannot fix a dead engine.")
        if "ion drive" in fl.reason:
            out.append("Ion engines are very efficient but need ~800 W of power - impossible far from the Sun on small arrays.")
        if fl.cnt["brownout"]:
            out.append("Power: %d weeks ran short of power. Solar output falls with distance squared and with eclipses; "
                       "bigger arrays, batteries, an RTG or switching instruments off all trade mass, cost or science." % fl.cnt["brownout"])
        if fl.lost > 1:
            out.append("Data: %.0f Gb was overwritten because the recorder was full. Balance instrument data rate, "
                       "recorder size and downlink (dish size x transmitter power)." % fl.lost)
        elif c["down"] < c["data"] and fl.reached_orbit:
            out.append("Downlink (%.0f Gb/wk) was smaller than the data produced (%.0f Gb/wk): science sat in the recorder "
                       "instead of reaching Earth." % (c["down"], c["data"]))
        if fl.cnt["inst_fail"] or fl.cnt["storm"]:
            out.append("Reliability: %d instrument failures and %d solar storms. Radiation hardening and redundancy cost mass "
                       "and money but protect the whole investment." % (fl.cnt["inst_fail"], fl.cnt["storm"]))
        if "orbit decayed" in fl.reason:
            out.append("Station-keeping: this orbit needs about %.3f km/s every week. Reserve propellant for it up front." % m["dv_sk"])
        if fl.reached_orbit and fl.reserve > 0.2 * m["budget"] and fl.returned < m["goal"]:
            out.append("You finished with $%.0fM unspent while missing the science goal - spare budget could have bought "
                       "instruments, hardening or redundancy." % fl.reserve)
        if not out:
            out.append("Excellent balance of mass, power, data and money. Try a harder mission or a cheaper design for a "
                       "higher score!")
        return out[:6]


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()