#!/usr/bin/env python3
"""bpmn_tool.py — utilidades del skill disenar-procesos (solo librería estándar).

Subcomandos:
  build     spec.json -o modelo.bpmn     JSON de proceso -> BPMN 2.0 XML con diagrama (DI) auto-maquetado
  validate  modelo.bpmn|spec.json        reglas estructurales, soundness (token game) y guías 7PMG
  viewer    a.bpmn [b.bpmn ...] -o v.html  visor HTML (bpmn-js) con pestañas y descarga
  eventlog  log.csv --case C --activity A --timestamp T [--start S] [--resource R]
                                         mini process mining: variantes, cycle time, DFG, rework, handoffs
  flow      spec.json [--runs N]         flow analysis Monte Carlo: CT, TCT, CTE, coste, unit load, ρ, cuello de botella
  dmn       tabla.json                   verifica tablas DMN: solapes (hit U) y huecos (completitud C)

Tabla DMN (JSON): {"name": "...", "hit": "U", "completeness": "C",
  "inputs": [{"name": "monto", "type": "number", "domain": [0, 100000]}, {"name": "tipo", "type": "enum", "values": ["hotel", "comida"]}],
  "rules": [{"id": "R1", "when": {"monto": "[0..1000)", "tipo": ["hotel"]}, "then": {"aprobacion": "auto"}}]}
  Intervalos: [a..b] (a..b) [a..b) >=a <b =a  ·  "-" = cualquier valor.

Formato del spec JSON (resumen; ver `python3 bpmn_tool.py build --help-spec`).
"""
import argparse
import csv
import html
import itertools
import json
import re
import statistics
import sys
import uuid
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict, deque
from datetime import datetime

SPEC_HELP = r"""
{
  "id": "Process_alquiler", "name": "alquiler de equipos",
  "pools": [
    {"id": "P_BuildIT", "name": "BuildIT",
     "lanes": [{"id": "L_obra", "name": "Ingeniero de obra"}, {"id": "L_clerk", "name": "Administrativo"}],
     "nodes": [
       {"id": "S1", "type": "startEvent", "event": "none|message|timer|signal|conditional",
        "name": "Necesidad de equipo identificada", "lane": "L_obra"},
       {"id": "T1", "type": "userTask", "name": "Registrar solicitud", "lane": "L_obra",
        "marker": "loop|multi|multiSeq (opcional)", "doc": "texto (opcional)"},
       {"id": "G1", "type": "exclusiveGateway", "name": "¿Equipo disponible?", "lane": "L_clerk"},
       {"id": "B1", "type": "boundaryEvent", "attachedTo": "T1", "event": "timer", "interrupting": true,
        "name": "48 h sin respuesta", "lane": "L_obra"},
       {"id": "E1", "type": "endEvent", "event": "none|terminate|message|error|signal", "name": "Equipo entregado"}
     ],
     "flows": [{"from": "S1", "to": "T1"}, {"from": "G1", "to": "T2", "name": "disponible", "default": false}]
    },
    {"id": "P_Proveedor", "name": "Proveedor", "blackbox": true}
  ],
  "messages": [{"from": "T5", "to": "P_Proveedor", "name": "Orden de compra"}],
  "data": [{"id": "D1", "type": "dataObject|dataStore", "name": "Solicitud [aprobada]",
            "pool": "P_BuildIT", "inputs": ["T2"], "outputs": ["T1"]}],
  "annotations": [{"id": "A1", "text": "Regla: < 1.000 € no requiere aprobación", "attachedTo": "G1"}]
}
Datos: "outputs" = tareas que ESCRIBEN el objeto; "inputs" = tareas que lo LEEN.
Condiciones: flujo.condition (texto/expresión) y nodo.condition para eventos condicionales.
Análisis cuantitativo (subcomando flow): nodo.ct (cycle time con espera), nodo.pt (processing), nodo.cost (otros
costes), flujo.p (probabilidad de rama), boundary.p y boundary.ct; y a nivel raíz:
  "flow": {"time_unit": "h", "hours_per_day": 8, "arrival_rate": 12, "roles": {"L_clerk": {"size": 3, "rate": 25}}}
El límite 7PMG G7 (30 elementos) cuenta flow objects por pool, sin boundary events ni pools black box.
Tipos de nodo: startEvent, endEvent, intermediateCatchEvent, intermediateThrowEvent, boundaryEvent,
task, userTask, serviceTask, scriptTask, sendTask, receiveTask, manualTask, businessRuleTask,
callActivity, subProcess (collapsed), adHocSubProcess, exclusiveGateway, parallelGateway,
inclusiveGateway, eventBasedGateway.
Eventos: none, message, timer, error, signal, terminate, conditional, escalation, compensate.
"""

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
NS = {
    "bpmn": BPMN_NS,
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

ACTIVITIES = {"task", "userTask", "serviceTask", "scriptTask", "sendTask", "receiveTask",
              "manualTask", "businessRuleTask", "callActivity", "subProcess", "adHocSubProcess"}
EVENTS = {"startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent", "boundaryEvent"}
GATEWAYS = {"exclusiveGateway", "parallelGateway", "inclusiveGateway", "eventBasedGateway"}
SIZE = {"activity": (100, 80), "event": (36, 36), "gateway": (50, 50)}
COL_W, ROW_H, LANE_MIN_H, LABEL_BAND, DATA_BAND = 140, 115, 140, 30, 75


def kind(t):
    if t in ACTIVITIES:
        return "activity"
    if t in EVENTS:
        return "event"
    if t in GATEWAYS:
        return "gateway"
    raise ValueError(f"Tipo de nodo desconocido: {t}")


def esc(s):
    return html.escape(str(s or ""), quote=True)


# ----------------------------------------------------------------------------- spec -> graph
def load_spec(path):
    with open(path, encoding="utf-8") as fh:
        spec = json.load(fh)
    spec.setdefault("id", "Process_1")
    spec.setdefault("name", "proceso")
    for p in spec.get("pools", []):
        p.setdefault("lanes", [])
        p.setdefault("nodes", [])
        p.setdefault("flows", [])
        for i, f in enumerate(p["flows"]):
            f.setdefault("id", f"Flow_{p['id']}_{i + 1}")
    for i, m in enumerate(spec.setdefault("messages", [])):
        m.setdefault("id", f"MsgFlow_{i + 1}")
    spec.setdefault("data", [])
    spec.setdefault("annotations", [])
    return spec


# ----------------------------------------------------------------------------- layout
def layout_pool(pool, data_items):
    nodes = {n["id"]: n for n in pool["nodes"]}
    flows = pool["flows"]
    succ, pred = defaultdict(list), defaultdict(list)
    for f in flows:
        succ[f["from"]].append(f["to"])
        pred[f["to"]].append(f["from"])
    # boundary events: rank like host
    hosts = {n["id"]: n["attachedTo"] for n in pool["nodes"] if n["type"] == "boundaryEvent"}
    # detect back edges with DFS from starts (and any unvisited node)
    starts = [nid for nid, n in nodes.items() if n["type"] == "startEvent"] or list(nodes)
    color, back = {}, set()

    def dfs(u):
        color[u] = 1
        nexts = list(succ[u])
        if u in hosts.values():
            nexts += [b for b, h in hosts.items() if h == u]
        for v in nexts:
            if color.get(v) == 1:
                back.add((u, v))
            elif v not in color:
                dfs(v)
        color[u] = 2

    sys.setrecursionlimit(10000)
    for s in starts + list(nodes):
        if s not in color:
            dfs(s)
    rank = {}
    indeg = defaultdict(int)
    adj = defaultdict(list)
    for f in flows:
        if (f["from"], f["to"]) not in back:
            adj[f["from"]].append(f["to"])
            indeg[f["to"]] += 1
    for b, h in hosts.items():  # arista implícita host -> boundary (mismo rango)
        if (h, b) not in back:
            adj[h].append(b)
            indeg[b] += 1
    order, q = [], deque([n for n in nodes if indeg[n] == 0])
    while q:
        u = q.popleft()
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    for u in order:
        rank.setdefault(u, 0)
        for v in adj[u]:
            step = 0 if hosts.get(v) == u else 1
            rank[v] = max(rank.get(v, 0), rank[u] + step)
    for n in nodes:
        rank.setdefault(n, rank.get(hosts.get(n), 0))
    lanes = pool["lanes"] or [{"id": f"{pool['id']}_lane", "name": ""}]
    lane_ids = [l["id"] for l in lanes]
    for n in pool["nodes"]:
        if n["type"] == "boundaryEvent":
            n["lane"] = nodes[n["attachedTo"]].get("lane", lane_ids[0])
        if n.get("lane") not in lane_ids:
            n["lane"] = lane_ids[0]
    cells = defaultdict(list)
    for n in pool["nodes"]:
        if n["type"] != "boundaryEvent":
            cells[(n["lane"], rank[n["id"]])].append(n["id"])
    rows_in_lane = {l: max([len(v) for (ln, _), v in cells.items() if ln == l] or [1]) for l in lane_ids}
    has_data = {l: any(d.get("lane") == l for d in data_items) for l in lane_ids}
    return rank, lane_ids, cells, rows_in_lane, has_data, back


def compute_geometry(spec):
    geo, lane_geo, pool_geo = {}, {}, {}
    y = 20
    max_rank = 0
    pool_layouts = {}
    for p in spec["pools"]:
        if p.get("blackbox"):
            continue
        items = [d for d in spec["data"] if d.get("pool") == p["id"]]
        # place data in lane of first related node
        nodes = {n["id"]: n for n in p["nodes"]}
        for d in items:
            rel = (d.get("outputs") or []) + (d.get("inputs") or [])
            d.setdefault("lane", nodes[rel[0]].get("lane") if rel and rel[0] in nodes else None)
        lay = layout_pool(p, items)
        pool_layouts[p["id"]] = lay
        max_rank = max([max_rank] + list(lay[0].values()))
    width = 2 * LABEL_BAND + 80 + (max_rank + 1) * COL_W
    for p in spec["pools"]:
        if p.get("blackbox"):
            continue
        rank, lane_ids, cells, rows_in_lane, has_data, _ = pool_layouts[p["id"]]
        nodes = {n["id"]: n for n in p["nodes"]}
        py = y
        for lid in lane_ids:
            band = DATA_BAND if has_data[lid] else 0
            h = max(LANE_MIN_H, rows_in_lane[lid] * ROW_H + 30) + band
            lane_geo[lid] = (20 + LABEL_BAND, y, width - LABEL_BAND, h)
            for (ln, r), ids in cells.items():
                if ln != lid:
                    continue
                for i, nid in enumerate(ids):
                    w, hh = SIZE[kind(nodes[nid]["type"])]
                    cx = 20 + 2 * LABEL_BAND + 60 + r * COL_W
                    cy = y + band + 20 + i * ROW_H + ROW_H // 2 - 10
                    geo[nid] = (cx - w / 2, cy - hh / 2, w, hh)
            y += h
        pool_geo[p["id"]] = (20, py, width, y - py)
        for n in p["nodes"]:
            if n["type"] == "boundaryEvent":
                hx, hy, hw, hh = geo[n["attachedTo"]]
                k = sum(1 for m in p["nodes"] if m["type"] == "boundaryEvent"
                        and m["attachedTo"] == n["attachedTo"] and m["id"] < n["id"])
                geo[n["id"]] = (hx + hw - 30 - k * 40, hy + hh - 18, 36, 36)
        placed = defaultdict(list)  # lane -> x positions already used
        for d in spec["data"]:
            if d.get("pool") != p["id"]:
                continue
            rel = [x for x in (d.get("outputs") or []) + (d.get("inputs") or []) if x in geo]
            lane_key = d.get("lane") if d.get("lane") in lane_geo else lane_ids[0]
            lx, ly, _, _ = lane_geo[lane_key]
            x = geo[rel[0]][0] + 70 if rel else lx + 80
            while any(abs(x - px) < 45 for px in placed[lane_key]):
                x += 45
            placed[lane_key].append(x)
            geo[d["id"]] = (x, ly + 10, 36, 50)
        y += 30
    for p in spec["pools"]:
        if p.get("blackbox"):
            pool_geo[p["id"]] = (20, y, width, 70)
            y += 100
    for i, a in enumerate(spec["annotations"]):
        t = geo.get(a.get("attachedTo"))
        geo[a["id"]] = ((t[0] + 20, t[1] - 70, 160, 45) if t else (40 + i * 180, y, 160, 45))
    return geo, lane_geo, pool_geo, pool_layouts


def mid(b):
    return (b[0] + b[2] / 2, b[1] + b[3] / 2)


def route(sb, tb, is_back):
    sx, sy = mid(sb)
    tx, ty = mid(tb)
    if is_back:
        out_y = max(sb[1] + sb[3], tb[1] + tb[3]) + 25
        return [(sx, sb[1] + sb[3]), (sx, out_y), (tx, out_y), (tx, tb[1] + tb[3])]
    start = (sb[0] + sb[2], sy)
    end = (tb[0], ty)
    if abs(sy - ty) < 1:
        return [start, end]
    if tb[0] > sb[0] + sb[2]:
        mx = (start[0] + end[0]) / 2
        return [start, (mx, sy), (mx, ty), end]
    return [(sx, sb[1] + sb[3] if ty > sy else sb[1]), (sx, ty), end]


# ----------------------------------------------------------------------------- build xml
def event_def(ev, nid, cond=None):
    ev = (ev or "none").lower()
    tag = {
        "message": "messageEventDefinition", "timer": "timerEventDefinition",
        "error": "errorEventDefinition", "signal": "signalEventDefinition",
        "terminate": "terminateEventDefinition", "conditional": "conditionalEventDefinition",
        "escalation": "escalationEventDefinition", "compensate": "compensateEventDefinition",
    }.get(ev)
    if not tag:
        return ""
    if tag == "conditionalEventDefinition":
        return (f'<bpmn:{tag} id="{nid}_ed"><bpmn:condition xsi:type="bpmn:tFormalExpression">'
                f'{esc(cond or "true")}</bpmn:condition></bpmn:{tag}>')
    return f'<bpmn:{tag} id="{nid}_ed"/>'


def build_xml(spec):
    geo, lane_geo, pool_geo, pool_layouts = compute_geometry(spec)
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<bpmn:definitions xmlns:bpmn="%s" xmlns:bpmndi="%s" xmlns:dc="%s" xmlns:di="%s" xmlns:xsi="%s" '
           'id="Defs_%s" targetNamespace="http://bpmn.io/schema/bpmn" exporter="disenar-procesos bpmn_tool" '
           'exporterVersion="1.0">' % (NS["bpmn"], NS["bpmndi"], NS["dc"], NS["di"], NS["xsi"],
                                       uuid.uuid4().hex[:8])]
    collab_id = f"Collab_{spec['id']}"
    out.append(f'<bpmn:collaboration id="{collab_id}">')
    proc_ids = {}
    for p in spec["pools"]:
        pid = f"Proc_{p['id']}"
        proc_ids[p["id"]] = pid
        ref = "" if p.get("blackbox") else f' processRef="{pid}"'
        out.append(f'<bpmn:participant id="{p["id"]}" name="{esc(p["name"])}"{ref}/>')
    for m in spec["messages"]:
        out.append(f'<bpmn:messageFlow id="{m["id"]}" name="{esc(m.get("name"))}" '
                   f'sourceRef="{m["from"]}" targetRef="{m["to"]}"/>')
    for a in spec["annotations"]:
        out.append(f'<bpmn:textAnnotation id="{a["id"]}"><bpmn:text>{esc(a["text"])}</bpmn:text></bpmn:textAnnotation>')
        if a.get("attachedTo"):
            out.append(f'<bpmn:association id="{a["id"]}_as" sourceRef="{a["attachedTo"]}" targetRef="{a["id"]}"/>')
    out.append("</bpmn:collaboration>")
    for p in spec["pools"]:
        if p.get("blackbox"):
            continue
        pid = proc_ids[p["id"]]
        out.append(f'<bpmn:process id="{pid}" name="{esc(spec["name"] if p is spec["pools"][0] else p["name"])}" isExecutable="false">')
        lanes = p["lanes"] or [{"id": f"{p['id']}_lane", "name": ""}]
        out.append(f'<bpmn:laneSet id="{p["id"]}_ls">')
        for l in lanes:
            refs = "".join(f"<bpmn:flowNodeRef>{n['id']}</bpmn:flowNodeRef>" for n in p["nodes"]
                           if n.get("lane") == l["id"])
            out.append(f'<bpmn:lane id="{l["id"]}" name="{esc(l["name"])}">{refs}</bpmn:lane>')
        out.append("</bpmn:laneSet>")
        incoming, outgoing = defaultdict(list), defaultdict(list)
        for f in p["flows"]:
            outgoing[f["from"]].append(f["id"])
            incoming[f["to"]].append(f["id"])
        defaults = {f["from"]: f["id"] for f in p["flows"] if f.get("default")}
        for n in p["nodes"]:
            t, nid = n["type"], n["id"]
            attrs = f'id="{nid}" name="{esc(n.get("name"))}"'
            if t in GATEWAYS and nid in defaults:
                attrs += f' default="{defaults[nid]}"'
            if t == "boundaryEvent":
                attrs += f' attachedToRef="{n["attachedTo"]}" cancelActivity="{str(n.get("interrupting", True)).lower()}"'
            if t == "startEvent" and n.get("interrupting") is False:
                attrs += ' isInterrupting="false"'
            inner = ""
            if n.get("doc"):
                inner += f"<bpmn:documentation>{esc(n['doc'])}</bpmn:documentation>"
            inner += "".join(f"<bpmn:incoming>{x}</bpmn:incoming>" for x in incoming[nid])
            inner += "".join(f"<bpmn:outgoing>{x}</bpmn:outgoing>" for x in outgoing[nid])
            for d in spec["data"]:
                if nid in (d.get("inputs") or []):
                    inner += (f'<bpmn:dataInputAssociation id="{nid}_{d["id"]}_in"><bpmn:sourceRef>{d["id"]}_ref'
                              f'</bpmn:sourceRef></bpmn:dataInputAssociation>')
                if nid in (d.get("outputs") or []):
                    inner += (f'<bpmn:dataOutputAssociation id="{nid}_{d["id"]}_out"><bpmn:targetRef>{d["id"]}_ref'
                              f'</bpmn:targetRef></bpmn:dataOutputAssociation>')
            marker = n.get("marker")
            if marker == "loop":
                inner += f'<bpmn:standardLoopCharacteristics id="{nid}_lc"/>'
            elif marker in ("multi", "multiSeq"):
                seq = "true" if marker == "multiSeq" else "false"
                inner += f'<bpmn:multiInstanceLoopCharacteristics id="{nid}_mi" isSequential="{seq}"/>'
            if t in EVENTS:
                inner += event_def(n.get("event"), nid, n.get("condition"))
            tag = "subProcess" if t == "subProcess" else t
            out.append(f"<bpmn:{tag} {attrs}>{inner}</bpmn:{tag}>")
        for f in p["flows"]:
            cond = ""
            if f.get("condition"):
                cond = f'<bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">{esc(f["condition"])}</bpmn:conditionExpression>'
            out.append(f'<bpmn:sequenceFlow id="{f["id"]}" name="{esc(f.get("name"))}" sourceRef="{f["from"]}" '
                       f'targetRef="{f["to"]}">{cond}</bpmn:sequenceFlow>')
        for d in spec["data"]:
            if d.get("pool") != p["id"]:
                continue
            if d.get("type") == "dataStore":
                out.append(f'<bpmn:dataStoreReference id="{d["id"]}_ref" name="{esc(d["name"])}"/>')
            else:
                out.append(f'<bpmn:dataObject id="{d["id"]}_obj"/>')
                out.append(f'<bpmn:dataObjectReference id="{d["id"]}_ref" name="{esc(d["name"])}" dataObjectRef="{d["id"]}_obj"/>')
        out.append("</bpmn:process>")
    # ---------------- DI
    out.append(f'<bpmndi:BPMNDiagram id="Diagram_{spec["id"]}"><bpmndi:BPMNPlane id="Plane_{spec["id"]}" bpmnElement="{collab_id}">')

    def shape(eid, b, extra=""):
        out.append(f'<bpmndi:BPMNShape id="{eid}_di" bpmnElement="{eid}"{extra}>'
                   f'<dc:Bounds x="{b[0]:.0f}" y="{b[1]:.0f}" width="{b[2]:.0f}" height="{b[3]:.0f}"/></bpmndi:BPMNShape>')

    def edge(eid, pts):
        wp = "".join(f'<di:waypoint x="{x:.0f}" y="{y:.0f}"/>' for x, y in pts)
        out.append(f'<bpmndi:BPMNEdge id="{eid}_di" bpmnElement="{eid}">{wp}</bpmndi:BPMNEdge>')

    for p in spec["pools"]:
        shape(p["id"], pool_geo[p["id"]], ' isHorizontal="true"')
        if p.get("blackbox"):
            continue
        for l in (p["lanes"] or [{"id": f"{p['id']}_lane"}]):
            shape(l["id"], lane_geo[l["id"]], ' isHorizontal="true"')
        for n in p["nodes"]:
            extra = ' isMarkerVisible="true"' if n["type"] == "exclusiveGateway" else ""
            if n["type"] in ("subProcess", "adHocSubProcess", "callActivity"):
                extra = ' isExpanded="false"'
            shape(n["id"], geo[n["id"]], extra)
        back = pool_layouts[p["id"]][5]
        for f in p["flows"]:
            edge(f["id"], route(geo[f["from"]], geo[f["to"]], (f["from"], f["to"]) in back))
        for d in spec["data"]:
            if d.get("pool") != p["id"]:
                continue
            shape(f'{d["id"]}_ref', geo[d["id"]])
            for t in d.get("inputs") or []:
                if t in geo:
                    edge(f'{t}_{d["id"]}_in', [mid(geo[d["id"]]), mid(geo[t])])
            for t in d.get("outputs") or []:
                if t in geo:
                    edge(f'{t}_{d["id"]}_out', [mid(geo[t]), mid(geo[d["id"]])])
    for m in spec["messages"]:
        sb = geo.get(m["from"]) or pool_geo[m["from"]]
        tb = geo.get(m["to"]) or pool_geo[m["to"]]
        sx = mid(sb)[0] if m["from"] in geo else mid(tb)[0]
        tx = mid(tb)[0] if m["to"] in geo else sx
        down = tb[1] > sb[1]
        sy = sb[1] + sb[3] if down else sb[1]
        ty = tb[1] if down else tb[1] + tb[3]
        pts = [(sx, sy), (tx, ty)] if abs(sx - tx) < 1 else [(sx, sy), (sx, (sy + ty) / 2), (tx, (sy + ty) / 2), (tx, ty)]
        edge(m["id"], pts)
    for a in spec["annotations"]:
        shape(a["id"], geo[a["id"]])
        if a.get("attachedTo") in geo:
            edge(f'{a["id"]}_as', [mid(geo[a["attachedTo"]]), (geo[a["id"]][0], geo[a["id"]][1] + 22)])
    out.append("</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>")
    return "\n".join(out)


# ----------------------------------------------------------------------------- graph model for validation
class Graph:
    def __init__(self):
        self.pools = []  # dict(id,name,nodes{id:{type,name,event,attachedTo,interrupting}}, flows[(id,src,tgt,name,cond,default)])
        self.messages = []
        self.defaults = {}


def graph_from_spec(spec):
    g = Graph()
    for p in spec["pools"]:
        if p.get("blackbox"):
            continue
        nodes = {n["id"]: dict(n) for n in p["nodes"]}
        flows = [(f["id"], f["from"], f["to"], f.get("name", ""), f.get("condition", ""), bool(f.get("default")))
                 for f in p["flows"]]
        g.pools.append({"id": p["id"], "name": p.get("name", p["id"]), "nodes": nodes, "flows": flows})
    g.messages = [(m["id"], m["from"], m["to"]) for m in spec["messages"]]
    g.all_pools = {p["id"] for p in spec["pools"]}
    g.node_pool = {n["id"]: p["id"] for p in spec["pools"] for n in p.get("nodes", [])}
    return g


def graph_from_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    b = "{%s}" % BPMN_NS
    g = Graph()
    proc_to_pool = {}
    g.all_pools = set()
    for part in root.iter(b + "participant"):
        g.all_pools.add(part.get("id"))
        if part.get("processRef"):
            proc_to_pool[part.get("processRef")] = (part.get("id"), part.get("name") or part.get("id"))
    g.node_pool = {}
    for proc in root.iter(b + "process"):
        pid, pname = proc_to_pool.get(proc.get("id"), (proc.get("id"), proc.get("name") or proc.get("id")))
        nodes, flows = {}, []
        defaults = {}
        for el in proc:
            t = el.tag.replace(b, "")
            if t in ACTIVITIES or t in EVENTS or t in GATEWAYS:
                ev = "none"
                for child in el:
                    ct = child.tag.replace(b, "")
                    if ct.endswith("EventDefinition"):
                        ev = ct.replace("EventDefinition", "")
                n = {"type": t, "name": el.get("name", ""), "event": ev}
                if t == "boundaryEvent":
                    n["attachedTo"] = el.get("attachedToRef")
                    n["interrupting"] = el.get("cancelActivity", "true") == "true"
                nodes[el.get("id")] = n
                g.node_pool[el.get("id")] = pid
                if el.get("default"):
                    defaults[el.get("default")] = True
            elif t == "sequenceFlow":
                cond = el.find(b + "conditionExpression")
                flows.append((el.get("id"), el.get("sourceRef"), el.get("targetRef"), el.get("name", ""),
                              (cond.text or "") if cond is not None else "", False))
        flows = [(i, s, t, n, c, i in defaults) for (i, s, t, n, c, _) in flows]
        g.pools.append({"id": pid, "name": pname, "nodes": nodes, "flows": flows})
    for mf in root.iter(b + "messageFlow"):
        g.messages.append((mf.get("id"), mf.get("sourceRef"), mf.get("targetRef")))
    return g


# ----------------------------------------------------------------------------- validation
STOP = set("""a al de del la las el los un una unos unas y o u en por para con sin al e the of to and or for in on with from
lo su sus se que""".split())
GENERIC = {"hacer", "realizar", "efectuar", "gestionar", "procesar", "tramitar", "ejecutar", "llevar",
           "do", "perform", "handle", "process", "manage", "make", "execute", "conduct"}


def explore(pool, start_id, max_states=20000):
    nodes, flows = pool["nodes"], pool["flows"]
    out_f, in_f = defaultdict(list), defaultdict(list)
    for fid, s, t, *_ in flows:
        out_f[s].append(fid)
        in_f[t].append(fid)
    tgt = {fid: t for fid, s, t, *_ in flows}
    boundary = defaultdict(list)
    for nid, n in nodes.items():
        if n["type"] == "boundaryEvent" and n.get("attachedTo"):
            boundary[n["attachedTo"]].append(nid)
    # reachability of flows from flows (for OR-join)
    reach_cache = {}

    def flows_reachable(fid):
        if fid in reach_cache:
            return reach_cache[fid]
        seen, dq = {fid}, deque([fid])
        while dq:
            f = dq.popleft()
            n = tgt[f]
            nexts = list(out_f[n]) + [x for bnode in boundary.get(n, []) for x in out_f[bnode]]
            for o in nexts:
                if o not in seen:
                    seen.add(o)
                    dq.append(o)
        reach_cache[fid] = seen
        return seen

    def cap(m):
        return tuple(sorted((k, min(v, 3)) for k, v in m.items() if v > 0))

    src_of = {fid: s for fid, s, t, *_ in flows}

    def fname(f):
        return f"{src_of[f]}→{tgt[f]}"

    # flujos exclusivos de ramas de boundary NO interruptores: varios tokens ahí son legítimos
    # (cada activación lanza su propio aviso hasta su end event; terminación implícita)
    main_reach = set()
    dqm = deque(out_f[start_id])
    while dqm:
        f = dqm.popleft()
        if f in main_reach:
            continue
        main_reach.add(f)
        n = tgt[f]
        nexts = list(out_f[n]) + [x for b2 in boundary.get(n, []) if nodes[b2].get("interrupting", True)
                                  for x in out_f[b2]]
        dqm.extend(nexts)
    nonint_only = set()
    for b2, n in nodes.items():
        if n["type"] == "boundaryEvent" and not n.get("interrupting", True):
            for f0 in out_f[b2]:
                nonint_only |= {x for x in flows_reachable(f0) if x not in main_reach}
                nonint_only.add(f0)
    max_tokens = {}

    init = Counter({f: 1 for f in out_f[start_id]})
    fired_nodes = {start_id}
    issues = set()
    start = cap(init)
    seen, dq = {start: None}, deque([start])
    edges = defaultdict(set)
    complete_states = set()
    while dq and len(seen) < max_states:
        st = dq.popleft()
        m = Counter(dict(st))
        if not m:
            complete_states.add(st)
            continue
        for f, v in m.items():
            if v > 1 and f not in nonint_only:
                max_tokens[f] = max(max_tokens.get(f, 0), v)
        succs = []
        for nid, n in nodes.items():
            t = n["type"]
            if t in ("startEvent", "boundaryEvent"):
                continue
            ins = in_f[nid]
            marked = [f for f in ins if m[f] > 0]
            if not marked:
                continue
            outs = out_f[nid]
            results = []
            if t == "parallelGateway":
                if all(m[f] > 0 for f in ins):
                    results.append((ins, [outs]))
            elif t == "inclusiveGateway" and len(ins) > 1:
                others = [f for f, v in m.items() if v > 0 and f not in ins]
                waiting = [f for f in ins if m[f] == 0 and any(f in flows_reachable(o) for o in others)]
                if not waiting:
                    choices = [list(c) for r in range(1, len(outs) + 1) for c in itertools.combinations(outs, r)] if len(outs) > 1 else [outs]
                    results.append((marked, choices))
            elif t in ("exclusiveGateway", "eventBasedGateway") or (t == "inclusiveGateway" and len(ins) <= 1):
                if t == "inclusiveGateway":
                    choices = [list(c) for r in range(1, len(outs) + 1) for c in itertools.combinations(outs, r)]
                else:
                    choices = [[o] for o in outs] or [[]]
                for f in marked:
                    results.append(([f], choices))
            else:  # activity / intermediate / end: XOR-join implícito, AND-split implícito
                for f in marked:
                    choices = [outs]
                    for bnode in boundary.get(nid, []):
                        bo = out_f[bnode]
                        if nodes[bnode].get("interrupting", True):
                            choices.append(bo)
                        else:
                            choices.append(outs + bo)
                    results.append(([f], choices))
            for consume, choices in results:
                for ch in choices:
                    m2 = Counter(m)
                    for f in consume:
                        m2[f] -= 1
                    if t == "endEvent" and str(n.get("event", "")).lower() == "terminate":
                        m2 = Counter()
                    for o in ch:
                        m2[o] += 1
                    succs.append((nid, cap(m2)))
        if not succs:
            names = ", ".join(sorted(fname(f) for f in m))
            issues.add(("deadlock", f"deadlock: los tokens quedan atascados en {names}"))
            continue
        for nid, s2 in succs:
            fired_nodes.add(nid)
            for bnode in boundary.get(nid, []):
                fired_nodes.add(bnode)
            edges[st].add(s2)
            if s2 not in seen:
                seen[s2] = st
                dq.append(s2)
    truncated = len(seen) >= max_states
    for f, v in max_tokens.items():
        issues.add(("lack_of_sync", f"falta de sincronización: el flujo {fname(f)} llega a acumular {v}"
                                    f"{'+' if v >= 3 else ''} tokens (una actividad o el fin se ejecutaría varias veces)"))
    # option to complete: every state can reach a complete state
    rev = defaultdict(set)
    for a, bs in edges.items():
        for b2 in bs:
            rev[b2].add(a)
    can = set(complete_states)
    dq2 = deque(complete_states)
    while dq2:
        s = dq2.popleft()
        for p in rev[s]:
            if p not in can:
                can.add(p)
                dq2.append(p)
    stuck = [s for s in seen if s not in can and edges.get(s)]
    if stuck and not truncated:
        issues.add(("no_option_to_complete", "hay estados desde los que la instancia no puede completarse (por deadlock o livelock)"))
    return fired_nodes, issues, truncated


def validate(g):
    errors, warnings, info = [], [], []
    for p in g.pools:
        nodes, flows = p["nodes"], p["flows"]
        pname = p["name"]
        ins, outs = defaultdict(list), defaultdict(list)
        for fid, s, t, name, cond, dflt in flows:
            if s not in nodes or t not in nodes:
                errors.append(f"[{pname}] el flujo {fid} conecta nodos fuera del pool ({s}→{t}); usa message flow entre pools")
                continue
            outs[s].append((fid, t, name, cond, dflt))
            ins[t].append(fid)
        starts = [n for n, d in nodes.items() if d["type"] == "startEvent"]
        ends = [n for n, d in nodes.items() if d["type"] == "endEvent"]
        if not starts:
            errors.append(f"[{pname}] no hay start event")
        if not ends:
            errors.append(f"[{pname}] no hay end event")
        for nid, d in nodes.items():
            t, lbl = d["type"], f'{nid} "{d.get("name", "")}"'
            if t == "startEvent" and ins[nid]:
                errors.append(f"[{pname}] el start event {lbl} tiene flujos entrantes")
            if t == "endEvent" and outs[nid]:
                errors.append(f"[{pname}] el end event {lbl} tiene flujos salientes")
            if t in ACTIVITIES and (not ins[nid] or not outs[nid]):
                errors.append(f"[{pname}] la actividad {lbl} debe tener ≥1 flujo entrante y ≥1 saliente")
            if t in ("intermediateCatchEvent", "intermediateThrowEvent") and (not ins[nid] or not outs[nid]):
                errors.append(f"[{pname}] el evento intermedio {lbl} debe tener entrada y salida")
            if t == "boundaryEvent":
                if d.get("attachedTo") not in nodes:
                    errors.append(f"[{pname}] el boundary {lbl} no está adjunto a una actividad del pool")
                if not outs[nid] and str(d.get("event")) != "compensate":
                    errors.append(f"[{pname}] el boundary {lbl} no tiene exception flow")
            if t in GATEWAYS:
                ni, no = len(ins[nid]), len(outs[nid])
                if ni >= 2 and no >= 2:
                    warnings.append(f"[{pname}] gateway mixto {lbl} (split y join a la vez): sepáralo en dos")
                elif ni < 2 and no < 2:
                    errors.append(f"[{pname}] el gateway {lbl} no es split ni join (entradas={ni}, salidas={no})")
                if t in ("exclusiveGateway", "inclusiveGateway") and no >= 2:
                    for fid, tt, name, cond, dflt in outs[nid]:
                        if not (name or cond or dflt):
                            warnings.append(f"[{pname}] el flujo {fid} que sale del split {lbl} no tiene condición/etiqueta")
                if t in ("exclusiveGateway", "inclusiveGateway") and no >= 2 and ni == 1:
                    src = next(f[1] for f in flows if f[2] == nid)
                    if nodes.get(src, {}).get("type") in GATEWAYS:
                        warnings.append(f"[{pname}] el split {lbl} sigue directamente a otro gateway ({src}): "
                                        "falta la actividad de decisión que produce el dato")
                    elif nodes.get(src, {}).get("type") == "startEvent":
                        warnings.append(f"[{pname}] el split {lbl} sigue al start event: ¿qué actividad decide?")
                if t == "eventBasedGateway":
                    for fid, tt, *_ in outs[nid]:
                        if nodes[tt]["type"] not in ("intermediateCatchEvent", "receiveTask"):
                            errors.append(f"[{pname}] tras el event-based gateway {lbl} solo caben eventos catch o receive tasks ({tt})")
        # path from start to end
        fwd = set(starts)
        dq = deque(starts)
        bmap = defaultdict(list)
        for nid, d in nodes.items():
            if d["type"] == "boundaryEvent":
                bmap[d.get("attachedTo")].append(nid)
        while dq:
            u = dq.popleft()
            for _, v, *_ in outs[u]:
                if v not in fwd:
                    fwd.add(v)
                    dq.append(v)
            for b2 in bmap.get(u, []):
                if b2 not in fwd:
                    fwd.add(b2)
                    dq.append(b2)
        bwd = set(ends)
        dq = deque(ends)
        while dq:
            u = dq.popleft()
            for fid in ins[u]:
                s = next(f[1] for f in flows if f[0] == fid)
                for cand in [s] + ([nodes[s]["attachedTo"]] if nodes.get(s, {}).get("type") == "boundaryEvent" else []):
                    if cand not in bwd:
                        bwd.add(cand)
                        dq.append(cand)
            if nodes.get(u, {}).get("type") == "boundaryEvent" and nodes[u].get("attachedTo") not in bwd:
                pass
        for nid, d in nodes.items():
            if nid not in fwd:
                errors.append(f'[{pname}] {nid} "{d.get("name", "")}" no es alcanzable desde un start event')
            elif nid not in bwd and d["type"] != "boundaryEvent":
                errors.append(f'[{pname}] desde {nid} "{d.get("name", "")}" no se llega a ningún end event')
        # soundness
        fired_all, sound_issues, trunc = set(), set(), False
        for s in starts:
            fired, iss, tr = explore(p, s)
            fired_all |= fired
            sound_issues |= iss
            trunc |= tr
        for k, msg in sorted(sound_issues):
            errors.append(f"[{pname}] SOUNDNESS: {msg}")
        if trunc:
            warnings.append(f"[{pname}] espacio de estados truncado (modelo muy concurrente): soundness no concluyente")
        for nid, d in nodes.items():
            if d["type"] in ACTIVITIES and nid not in fired_all and nid in fwd:
                errors.append(f'[{pname}] SOUNDNESS: actividad muerta {nid} "{d.get("name", "")}" (nunca se ejecuta)')
        # 7PMG
        flow_objs = [n for n, d in nodes.items() if d["type"] != "boundaryEvent"]
        if len(flow_objs) > 30:
            warnings.append(f"[{pname}] 7PMG G7: {len(flow_objs)} elementos (>30): descompón en subprocesos")
        for nid, d in nodes.items():
            deg = len(ins[nid]) + len(outs[nid])
            if deg > 4:
                warnings.append(f'[{pname}] 7PMG G2: {nid} tiene {deg} caminos de entrada/salida')
        ors = [n for n, d in nodes.items() if d["type"] == "inclusiveGateway"]
        if ors:
            warnings.append(f"[{pname}] 7PMG G5: {len(ors)} gateway(s) OR ({', '.join(ors)}): evítalos si es posible")
        info.append(f"[{pname}] 7PMG G3: {len(starts)} start(s), {len(ends)} end(s) — uno por disparador / uno por outcome")
        for nid, d in nodes.items():
            name = (d.get("name") or "").strip()
            t = d["type"]
            if t in ACTIVITIES:
                if not name:
                    warnings.append(f"[{pname}] 7PMG G6: actividad {nid} sin etiqueta")
                    continue
                words = [w for w in re.findall(r"[\wáéíóúñü]+", name.lower()) if w not in STOP]
                if len(words) > 5:
                    warnings.append(f'[{pname}] etiqueta larga ({len(words)} palabras): "{name}" (máx. ~5)')
                if words and words[0] in GENERIC:
                    warnings.append(f'[{pname}] 7PMG G6: verbo genérico en "{name}"; usa verbo específico + objeto')
                if words and re.search(r"(ción|sión|miento|ing)$", words[0]):
                    warnings.append(f'[{pname}] 7PMG G6: "{name}" parece estilo acción-sustantivo; usa verbo en infinitivo/imperativo + objeto')
            if t in ("startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent") and not name:
                warnings.append(f"[{pname}] evento {nid} sin etiqueta (usa objeto + participio)")
    pools_with_nodes = {p["id"] for p in g.pools}
    for mid_, s, t in g.messages:
        ps = g.node_pool.get(s, s if s in g.all_pools else None)
        pt = g.node_pool.get(t, t if t in g.all_pools else None)
        if ps is None or pt is None:
            errors.append(f"message flow {mid_}: origen o destino inexistente ({s}→{t})")
        elif ps == pt:
            errors.append(f"message flow {mid_} conecta elementos del mismo pool; usa sequence flow")
    return errors, warnings, info


# ----------------------------------------------------------------------------- viewer
VIEWER = r"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>__TITLE__</title>
<link rel="stylesheet" href="https://unpkg.com/bpmn-js@17.11.1/dist/assets/bpmn-js.css">
<style>
:root{--bg:#f7f7f5;--fg:#1d1d1b;--muted:#6b6b66;--card:#fff;--line:#ddd;--accent:#2f5d8a}
@media (prefers-color-scheme:dark){:root{--bg:#1b1c1e;--fg:#ececea;--muted:#a0a09a;--card:#26272a;--line:#3a3b3e;--accent:#7fb0e0}}
body{margin:0;font:15px/1.4 system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--fg)}
header{padding:14px 16px;border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:center;flex-wrap:wrap}
h1{font-size:17px;margin:0;flex:1}
nav button,.act{border:1px solid var(--line);background:var(--card);color:var(--fg);padding:6px 12px;border-radius:6px;cursor:pointer;font:inherit}
nav button[aria-selected=true]{border-color:var(--accent);color:var(--accent);font-weight:600}
#canvas{height:calc(100vh - 64px);background:#fff}
.err{padding:0 16px;color:#b00}.err:empty{display:none}
</style></head><body>
<header><h1>__TITLE__</h1><nav id="tabs"></nav>
<button class="act" id="fit">Ajustar</button><button class="act" id="dl">Descargar .bpmn</button><button class="act" id="svg">Exportar SVG</button></header>
<div id="msg" class="err" role="status"></div><div id="canvas"></div>
<script src="https://unpkg.com/bpmn-js@17.11.1/dist/bpmn-navigated-viewer.production.min.js"></script>
<script>
const MODELS = __MODELS__;
const viewer = new BpmnJS({container:'#canvas'});
let current = 0;
function fit(){ try { viewer.get('canvas').zoom('fit-viewport', 'auto'); } catch(e) { setTimeout(fit, 150); } }
window.addEventListener('resize', fit);
async function show(i){
  current = i;
  document.querySelectorAll('#tabs button').forEach((b,j)=>b.setAttribute('aria-selected', j===i));
  document.getElementById('msg').textContent = '';
  try { await viewer.importXML(MODELS[i].xml); requestAnimationFrame(fit); }
  catch(e){ document.getElementById('msg').textContent = 'Error al cargar: ' + e.message; }
}
MODELS.forEach((m,i)=>{const b=document.createElement('button');b.textContent=m.name;b.onclick=()=>show(i);document.getElementById('tabs').appendChild(b);});
function save(name, data, type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([data],{type}));a.download=name;a.click();}
document.getElementById('fit').onclick=fit;
document.getElementById('dl').onclick=()=>save(MODELS[current].file, MODELS[current].xml, 'application/xml');
document.getElementById('svg').onclick=async()=>{const {svg}=await viewer.saveSVG();save(MODELS[current].file.replace(/\.bpmn$/,'.svg'), svg, 'image/svg+xml');};
show(0);
</script></body></html>"""


def make_viewer(files, out, title):
    models = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            xml = fh.read()
        name = re.sub(r"\.bpmn$", "", f.split("/")[-1])
        models.append({"name": name, "file": f.split("/")[-1], "xml": xml})
    page = VIEWER.replace("__TITLE__", html.escape(title)).replace(
        "__MODELS__", json.dumps(models, ensure_ascii=False).replace("</", "<\\/"))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page)


# ----------------------------------------------------------------------------- event log
FMTS = ["%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M", "%d/%m/%Y", "%m/%d/%Y %H:%M", "%d-%m-%Y %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"]


def parse_ts(s):
    s = s.strip().replace("Z", "+00:00") if s else s
    for f in FMTS:
        try:
            d = datetime.strptime(s, f)
            return d.replace(tzinfo=None)
        except (ValueError, TypeError):
            continue
    try:
        return datetime.fromisoformat(s).replace(tzinfo=None)
    except Exception:
        return None


def fmt_h(hours):
    if hours is None:
        return "-"
    if hours >= 48:
        return f"{hours / 24:.1f} d"
    if hours >= 1:
        return f"{hours:.1f} h"
    return f"{hours * 60:.0f} min"


def eventlog_report(path, case, act, ts, res=None, delim=None, top=10, mermaid=False, start=None):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        if not delim:
            try:
                delim = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
            except csv.Error:
                delim = ","
        rows = list(csv.DictReader(fh, delimiter=delim))
    if not rows:
        return "Log vacío."
    for c in [case, act, ts] + ([res] if res else []) + ([start] if start else []):
        if c not in rows[0]:
            raise SystemExit(f"Columna '{c}' no encontrada. Columnas: {list(rows[0].keys())}")
    traces, bad = defaultdict(list), 0
    for r in rows:
        t = parse_ts(r[ts])
        if t is None:
            bad += 1
            continue
        st = parse_ts(r[start]) if start and r.get(start) else None
        traces[r[case]].append((t, r[act].strip(), (r.get(res) or "").strip() if res else "", st))
    for k in traces:
        traces[k].sort(key=lambda x: x[0])
    n_cases, n_events = len(traces), sum(len(v) for v in traces.values())
    act_freq = Counter(a for v in traces.values() for _, a, *_ in v)
    act_cases = Counter(a for v in traces.values() for a in {e[1] for e in v})
    variants = Counter(tuple(a for _, a, *_ in v) for v in traces.values())
    cts = [(v[-1][0] - (v[0][3] or v[0][0])).total_seconds() / 3600 for v in traces.values()
           if len(v) > 1 or v[0][3]]
    dfg, delay = Counter(), defaultdict(list)
    handoff, hdelay = Counter(), defaultdict(list)
    rework_cases = Counter()
    for v in traces.values():
        seen = Counter(a for _, a, *_ in v)
        for a, c in seen.items():
            if c > 1:
                rework_cases[a] += 1
        for (t1, a1, r1, *_), (t2, a2, r2, s2) in zip(v, v[1:]):
            dfg[(a1, a2)] += 1
            # con --start la demora es la ESPERA (fin de a1 -> inicio de a2); sin él, fin -> fin
            delay[(a1, a2)].append(((s2 or t2) - t1).total_seconds() / 3600)
            if res and r1 and r2 and r1 != r2:
                handoff[(r1, r2)] += 1
                hdelay[(r1, r2)].append((t2 - t1).total_seconds() / 3600)
    starts = Counter(v[0][1] for v in traces.values())
    ends = Counter(v[-1][1] for v in traces.values())
    span = (min(v[0][0] for v in traces.values()), max(v[-1][0] for v in traces.values()))
    L = [f"# Informe de event log — `{path.split('/')[-1]}`", "",
         f"- **Casos**: {n_cases} · **Eventos**: {n_events} · **Actividades**: {len(act_freq)} · "
         f"**Variantes**: {len(variants)} · **Periodo**: {span[0]:%Y-%m-%d} → {span[1]:%Y-%m-%d}"]
    if bad:
        L.append(f"- ⚠️ {bad} filas descartadas por timestamp no reconocido")
    if cts:
        q = statistics.quantiles(cts, n=10) if len(cts) >= 10 else None
        L.append(f"- **Cycle time** (primer→último evento): media {fmt_h(statistics.mean(cts))} · "
                 f"mediana {fmt_h(statistics.median(cts))} · mín {fmt_h(min(cts))} · máx {fmt_h(max(cts))}"
                 + (f" · p90 {fmt_h(q[-1])}" if q else ""))
    if len(ends) > 1:
        L.append(f"- ⚠️ **Longevidad**: hay {len(ends)} actividades de fin distintas; los casos que no terminan en un fin "
                 f"esperado pueden estar incompletos y sesgan el CT ({', '.join(f'{a} ({c})' for a, c in ends.most_common(5))}).")
    if start:
        proc = defaultdict(list)
        for v in traces.values():
            for t, a, _, st in v:
                if st:
                    proc[a].append((t - st).total_seconds() / 3600)
        if proc:
            pt_case = statistics.mean(sum((t - st).total_seconds() / 3600 for t, _, _, st in v if st)
                                      for v in traces.values())
            line = f"- **Processing time** medio por caso {fmt_h(pt_case)}"
            if cts and statistics.mean(cts) > 0:
                line += f" → **CTE ≈ {pt_case / statistics.mean(cts):.1%}** (sin calendario laboral)"
            L.append(line)
    ptimes = defaultdict(list)
    for v in traces.values():
        for t, a, _, st in v:
            if st:
                ptimes[a].append((t - st).total_seconds() / 3600)
    L += ["", "## Actividades", "| Actividad | Eventos | % casos | Casos con repetición (rework) | Processing medio |",
          "|---|---|---|---|---|"]
    for a, c in act_freq.most_common():
        pm = fmt_h(statistics.mean(ptimes[a])) if ptimes.get(a) else "-"
        L.append(f"| {a} | {c} | {100 * act_cases[a] / n_cases:.0f}% | {rework_cases.get(a, 0)} | {pm} |")
    L += ["", f"**Actividades de inicio**: {', '.join(f'{a} ({c})' for a, c in starts.most_common())}",
          f"**Actividades de fin**: {', '.join(f'{a} ({c})' for a, c in ends.most_common())}",
          "", f"## Variantes (top {top})", "| # | Casos | % | Traza |", "|---|---|---|---|"]
    for i, (vr, c) in enumerate(variants.most_common(top), 1):
        L.append(f"| {i} | {c} | {100 * c / n_cases:.1f}% | {' → '.join(vr)} |")
    L += ["", "## Directly-follows (DFG) — frecuencia y demora media" + (" (espera: fin→inicio)" if start else " (fin→fin)"),
          "| De | A | Frecuencia | Demora media |", "|---|---|---|---|"]
    for (a1, a2), c in dfg.most_common(40):
        L.append(f"| {a1} | {a2} | {c} | {fmt_h(statistics.mean(delay[(a1, a2)]))} |")
    slow = sorted(dfg, key=lambda k: statistics.mean(delay[k]), reverse=True)[:5]
    L += ["", "**Posibles cuellos de botella (mayor demora entre actividades consecutivas)**: " +
          "; ".join(f"{a}→{b} ({fmt_h(statistics.mean(delay[(a, b)]))}, n={dfg[(a, b)]})" for a, b in slow)]
    if res:
        L += ["", "## Handoffs entre recursos (top 15)", "| De | A | Veces | Demora media |", "|---|---|---|---|"]
        for (r1, r2), c in handoff.most_common(15):
            L.append(f"| {r1} | {r2} | {c} | {fmt_h(statistics.mean(hdelay[(r1, r2)]))} |")
    # flexibility metrics
    tasks = set(act_freq)
    optional = {a for a in tasks if act_cases[a] < n_cases}
    L += ["", "## Métricas de flexibilidad y calidad",
          f"- **DE (ejecuciones distintas)** = {len(variants)} · **OPT** = {len(optional)}/{len(tasks)} = "
          f"{len(optional) / len(tasks):.2f}",
          "- **r (probabilidad de rework) por actividad** = 1 − T/CT ≈ 1 − (casos con la actividad / ejecuciones):"]
    for a in sorted(tasks, key=lambda x: -(1 - act_cases[x] / act_freq[x])):
        r = 1 - act_cases[a] / act_freq[a]
        if r > 0:
            L.append(f"  - {a}: r ≈ {r:.2f}")
    if mermaid:
        ids = {a: f"A{i}" for i, a in enumerate(sorted(tasks))}
        L += ["", "## DFG (Mermaid)", "```mermaid", "flowchart LR"]
        for a, i in ids.items():
            L.append(f'  {i}["{a} ({act_freq[a]})"]')
        thr = max(1, int(0.05 * n_cases))
        for (a1, a2), c in dfg.items():
            if c >= thr:
                L.append(f"  {ids[a1]} -->|{c}| {ids[a2]}")
        L.append("```")
        L.append(f"_Se ocultan arcos con frecuencia < {thr} (5 % de los casos)._")
    return "\n".join(L)



# ----------------------------------------------------------------------------- flow analysis (Monte Carlo)
def flow_analysis(spec, runs=5000, seed=7):
    """Simula casos aislados (sin contención) sobre el grafo: CT, TCT, CTE, coste, unit load, capacidad.
    Campos: nodo.ct (cycle time, incluye espera), nodo.pt (processing time), nodo.cost (otros costes),
    flujo.p (probabilidad de rama en XOR/OR; en OR cada salida se activa con p independiente),
    boundary.p (probabilidad de disparo) y boundary.ct (tiempo hasta el disparo, por defecto ct del host).
    spec["flow"] = {"time_unit": "h", "hours_per_day": 8, "arrival_rate": casos por día,
                    "roles": {"<lane id>": {"size": 3, "rate": 25}}}"""
    import random
    rnd = random.Random(seed)
    cfg = spec.get("flow", {})
    unit = cfg.get("time_unit", "h")
    roles = cfg.get("roles", {})
    pools = [p for p in spec["pools"] if not p.get("blackbox")]
    warn = []
    res = {"ct": [], "tct": [], "cost": [], "visits": Counter(), "load": Counter(), "ends": Counter()}
    for p in pools:
        nodes = {n["id"]: n for n in p["nodes"]}
        out_f, in_f = defaultdict(list), defaultdict(list)
        for f in p["flows"]:
            out_f[f["from"]].append(f)
            in_f[f["to"]].append(f)
        bnd = defaultdict(list)
        for n in p["nodes"]:
            if n["type"] == "boundaryEvent":
                bnd[n["attachedTo"]].append(n)
        for nid, n in nodes.items():
            outs = out_f[nid]
            if n["type"] in ("exclusiveGateway", "eventBasedGateway") and len(outs) > 1:
                ps = [f.get("p") for f in outs]
                if any(x is None for x in ps):
                    warn.append(f"{nid}: faltan probabilidades 'p' en sus salidas; se reparte el resto a partes iguales")
                elif abs(sum(ps) - 1) > 0.01:
                    warn.append(f"{nid}: las probabilidades suman {sum(ps):.2f} (≠ 1); se normalizan")
            if n["type"] in ACTIVITIES and "ct" not in n:
                warn.append(f"{nid} \"{n.get('name', '')}\": sin 'ct'; se asume 0")
        starts = [nid for nid, n in nodes.items() if n["type"] == "startEvent"]
        if not starts:
            continue

        def pick(outs):
            ps = [f.get("p") for f in outs]
            known = sum(x for x in ps if x is not None)
            unknown = [i for i, x in enumerate(ps) if x is None]
            ws = [x if x is not None else max(0.0, 1 - known) / len(unknown) for x in ps] if unknown else ps
            tot = sum(ws) or 1
            r, acc = rnd.random() * tot, 0
            for f, w in zip(outs, ws):
                acc += w
                if r <= acc:
                    return f
            return outs[-1]

        for _ in range(runs):
            pending = [(0.0, 0.0, f) for f in out_f[starts[0]]]  # (t_ct, t_pt, flow)
            joins = defaultdict(lambda: defaultdict(list))
            cost, end_t, end_pt, steps = 0.0, 0.0, 0.0, 0
            while pending and steps < 10000:
                steps += 1
                pending.sort(key=lambda x: x[0])
                t, tp, f = pending.pop(0)
                nid = f["to"]
                n = nodes[nid]
                typ = n["type"]
                outs = out_f[nid]
                if typ == "parallelGateway" and len(in_f[nid]) > 1:
                    joins[nid][f["id"]].append((t, tp))
                    if all(joins[nid][g["id"]] for g in in_f[nid]):
                        arr = [joins[nid][g["id"]].pop(0) for g in in_f[nid]]
                        t, tp = max(a[0] for a in arr), max(a[1] for a in arr)
                        pending += [(t, tp, o) for o in outs]
                    continue
                if typ == "inclusiveGateway" and len(in_f[nid]) > 1:
                    joins[nid][f["id"]].append((t, tp))
                    reach = set()
                    stack = [x[2]["to"] for x in pending]
                    while stack:
                        u = stack.pop()
                        if u in reach:
                            continue
                        reach.add(u)
                        stack += [o["to"] for o in out_f[u]] + [b["id"] for b in bnd.get(u, [])]
                    if nid not in reach:
                        arr = [a for g in in_f[nid] for a in joins[nid][g["id"]]]
                        for g in in_f[nid]:
                            joins[nid][g["id"]] = []
                        t, tp = max(a[0] for a in arr), max(a[1] for a in arr)
                        pending += [(t, tp, o) for o in outs]
                    continue
                res["visits"][nid] += 1
                if typ in ACTIVITIES:
                    ct, pt = float(n.get("ct", 0)), float(n.get("pt", n.get("ct", 0)))
                    lane = n.get("lane")
                    rate = roles.get(lane, {}).get("rate", 0)
                    cost += pt * rate + float(n.get("cost", 0))
                    res["load"][lane] += pt
                    fired = None
                    for b in bnd.get(nid, []):
                        if rnd.random() < float(b.get("p", 0)):
                            fired = b
                            break
                    if fired is not None and fired.get("interrupting", True):
                        bt = float(fired.get("ct", ct))
                        res["visits"][fired["id"]] += 1
                        pending += [(t + bt, tp + min(pt, bt), o) for o in out_f[fired["id"]]]
                        continue
                    if fired is not None:
                        bt = float(fired.get("ct", ct))
                        res["visits"][fired["id"]] += 1
                        pending += [(t + bt, tp, o) for o in out_f[fired["id"]]]
                    pending += [(t + ct, tp + pt, o) for o in outs]
                elif typ in ("exclusiveGateway", "eventBasedGateway") and len(outs) > 1:
                    pending.append((t, tp, pick(outs)))
                elif typ == "inclusiveGateway" and len(outs) > 1:
                    act = [o for o in outs if rnd.random() < float(o.get("p", 0.5))] or [pick(outs)]
                    pending += [(t, tp, o) for o in act]
                elif typ == "endEvent":
                    res["ends"][nid] += 1
                    end_t, end_pt = max(end_t, t), max(end_pt, tp)
                    if str(n.get("event", "")).lower() == "terminate":
                        pending = []
                else:
                    ct = float(n.get("ct", 0))
                    pending += [(t + ct, tp, o) for o in outs]
            res["ct"].append(end_t)
            res["tct"].append(end_pt)
            res["cost"].append(cost)
        break  # primer pool con nodos = proceso principal
    return res, warn, unit, cfg, runs


def flow_report(spec, runs=5000):
    res, warn, unit, cfg, runs = flow_analysis(spec, runs)
    if not res["ct"]:
        return "No hay start event en el pool principal."
    mean = statistics.mean
    ct, tct = mean(res["ct"]), mean(res["tct"])
    q = statistics.quantiles(res["ct"], n=10)
    if ct == 0:
        return ("# Flow analysis — sin datos de tiempo\n\nNinguna actividad del pool principal tiene `ct`/`pt`. "
                "Anota tiempos (`ct`, `pt`), probabilidades de rama (`p`) y el bloque `flow` en el JSON "
                "(ver `build --help-spec`) y vuelve a ejecutar.\n\n" + "\n".join(f"- {w}" for w in sorted(set(warn))[:15]))
    L = [f"# Flow analysis — {spec.get('name', '')}", "",
         f"_Monte Carlo de {runs} casos sin contención de recursos (ch07). Unidad de tiempo: {unit}._", "",
         "| Medida | Valor |", "|---|---|",
         f"| Cycle time medio (CT) | {ct:.2f} {unit} |", f"| CT mediana / p90 | {statistics.median(res['ct']):.2f} / {q[-1]:.2f} {unit} |",
         f"| Theoretical cycle time (TCT, solo processing) | {tct:.2f} {unit} |",
         f"| **Cycle time efficiency (CTE = TCT/CT)** | **{(tct / ct if ct else 0):.1%}** |",
         f"| Coste medio por caso | {mean(res['cost']):.2f} |"]
    nodes = {n["id"]: n for p in spec["pools"] for n in p.get("nodes", [])}
    L += ["", "## Ejecuciones esperadas por caso", "| Nodo | Nombre | Ejecuciones/caso |", "|---|---|---|"]
    for nid, v in sorted(res["visits"].items(), key=lambda x: -x[1]):
        if nodes.get(nid, {}).get("type") in ACTIVITIES or nodes.get(nid, {}).get("type") == "boundaryEvent":
            L.append(f"| {nid} | {nodes[nid].get('name', '')} | {v / runs:.2f} |")
    L += ["", "## Outcomes", "| End event | % casos |", "|---|---|"]
    for nid, v in res["ends"].most_common():
        L.append(f"| {nodes[nid].get('name', nid)} | {v / runs:.1%} |")
    roles, lam = cfg.get("roles", {}), cfg.get("arrival_rate")
    hpd = float(cfg.get("hours_per_day", 8))
    lanes = {l["id"]: l.get("name", l["id"]) for p in spec["pools"] for l in p.get("lanes", [])}
    L += ["", "## Unit load, capacidad y utilización (ch07 §7.1.5)",
          "| Rol (lane) | Unit load/caso | Tamaño | Capacidad teórica (casos/día) | ρ = λ/μ | ρ con −1 / +1 recurso |", "|---|---|---|---|---|---|"]
    caps = {}
    for lane, load in res["load"].items():
        ul = load / runs
        size = roles.get(lane, {}).get("size")
        if size and ul > 0:
            ul_h = ul if unit == "h" else (ul / 60 if unit == "min" else ul * hpd)
            mu = size * hpd / ul_h
            caps[lane] = mu
            rho = f"{lam / mu:.0%}" if lam else "-"
            alt = (f"{lam / ((size - 1) * hpd / ul_h):.0%} / {lam / ((size + 1) * hpd / ul_h):.0%}"
                   if lam and size > 1 else "-")
            L.append(f"| {lanes.get(lane, lane)} | {ul:.2f} {unit} | {size} | {mu:.1f} | {rho} | {alt} |")
        else:
            L.append(f"| {lanes.get(lane, lane)} | {ul:.2f} {unit} | - | - | - | - |")
    if caps:
        bn = min(caps, key=caps.get)
        L.append(f"\n**Cuello de botella**: {lanes.get(bn, bn)} (capacidad {caps[bn]:.1f} casos/día)"
                 + (f" · **Little**: WIP ≈ λ·CT = {lam * (ct if unit == 'd' else ct / hpd if unit == 'h' else ct / 60 / hpd):.1f} casos" if lam else ""))
    if warn:
        L += ["", "## Avisos de datos"] + [f"- {w}" for w in sorted(set(warn))]
    return "\n".join(L)


# ----------------------------------------------------------------------------- DMN table check
def _interval(expr):
    """'[a..b]', '(a..b)', '[a..b)', '>=a', '<b', '=a', 'a', '-' -> (lo, lo_inc, hi, hi_inc)."""
    e = str(expr).strip().replace(" ", "")
    inf = float("inf")
    if e in ("-", "", "*"):
        return (-inf, True, inf, True)
    m = re.match(r"^([\[\(\]])(-?[\d.]+)\.\.(-?[\d.]+)([\]\)\[])$", e)
    if m:
        return (float(m.group(2)), m.group(1) == "[", float(m.group(3)), m.group(4) == "]")
    m = re.match(r"^(>=|>|<=|<|=)?(-?[\d.]+)$", e)
    if m:
        op, v = m.group(1) or "=", float(m.group(2))
        return {">=": (v, True, inf, True), ">": (v, False, inf, True), "<=": (-inf, True, v, True),
                "<": (-inf, True, v, False), "=": (v, True, v, True)}[op]
    raise ValueError(f"Intervalo no reconocido: {expr}")


def _contains(iv, x):
    lo, li, hi, hi_ = iv
    return (x > lo or (li and x == lo)) and (x < hi or (hi_ and x == hi))


def dmn_check(table):
    hit = table.get("hit", "U").upper()
    comp = table.get("completeness", "C").upper()
    inputs = table["inputs"]
    rules = table["rules"]
    def cond(rule, inp):
        v = rule.get("when", {}).get(inp["name"], "-")
        if inp.get("type") == "enum":
            return None if v in ("-", "*", None) else (set(v) if isinstance(v, list) else {v})
        return _interval(v)
    def covers(rule, point):
        for inp, x in zip(inputs, point):
            c = cond(rule, inp)
            if inp.get("type") == "enum":
                if c is not None and x not in c:
                    return False
            elif not _contains(c, x):
                return False
        return True
    # representative points per input
    axes = []
    for inp in inputs:
        if inp.get("type") == "enum":
            axes.append(list(inp["values"]))
            continue
        lo, hi = inp.get("domain", [0, 1e9])
        bps = {float(lo), float(hi)}
        for r in rules:
            a, _, b, _ = cond(r, inp)
            for v in (a, b):
                if lo <= v <= hi:
                    bps.add(float(v))
        bps = sorted(bps)
        pts = []
        for i, bp in enumerate(bps):
            pts.append(bp)
            if i + 1 < len(bps):
                pts.append((bp + bps[i + 1]) / 2)
        axes.append(pts)
    overlaps, gaps = [], []
    for point in itertools.product(*axes):
        hits = [r.get("id", f"R{i + 1}") for i, r in enumerate(rules) if covers(r, point)]
        desc = ", ".join(f"{inp['name']}={x:g}" if isinstance(x, float) else f"{inp['name']}={x}"
                         for inp, x in zip(inputs, point))
        if not hits and comp == "C":
            gaps.append(desc)
        if len(hits) > 1 and hit == "U":
            overlaps.append((tuple(hits), desc))
    L = [f"# Verificación DMN — {table.get('name', '')}", f"Hit **{hit}** · completitud **{comp}** · "
         f"{len(rules)} reglas · {len(inputs)} entradas", ""]
    if overlaps:
        seen = {}
        for hs, d in overlaps:
            seen.setdefault(hs, d)
        L.append(f"## ✗ Reglas solapadas ({len(seen)} combinación(es) de reglas)")
        L += [f"- {' y '.join(hs)} coinciden, p. ej. en {d}" for hs, d in list(seen.items())[:20]]
    if gaps:
        L.append(f"## ✗ Reglas faltantes ({len(gaps)} puntos sin cubrir; ejemplos)")
        L += [f"- {g}" for g in gaps[:20]]
    if not overlaps and not gaps:
        L.append("✓ Sin solapamientos ni huecos en el dominio declarado.")
    return "\n".join(L), bool(overlaps or gaps)


# ----------------------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="spec JSON -> BPMN XML")
    b.add_argument("spec", nargs="?")
    b.add_argument("-o", "--out")
    b.add_argument("--help-spec", action="store_true")
    b.add_argument("--strict", action="store_true", help="no escribir el .bpmn si hay errores")
    v = sub.add_parser("validate", help="validar .bpmn o spec .json")
    v.add_argument("model")
    vw = sub.add_parser("viewer", help="visor HTML")
    vw.add_argument("models", nargs="+")
    vw.add_argument("-o", "--out", required=True)
    vw.add_argument("--title", default="Modelos de proceso")
    el = sub.add_parser("eventlog", help="análisis de event log CSV")
    el.add_argument("log")
    el.add_argument("--case", required=True)
    el.add_argument("--activity", required=True)
    el.add_argument("--timestamp", required=True)
    el.add_argument("--resource")
    el.add_argument("--start", help="columna con el timestamp de inicio (separa espera y procesamiento)")
    el.add_argument("--delimiter")
    el.add_argument("--top", type=int, default=10)
    el.add_argument("--mermaid", action="store_true")
    el.add_argument("-o", "--out")
    fl = sub.add_parser("flow", help="flow analysis Monte Carlo sobre el spec JSON (ct, pt, p, roles)")
    fl.add_argument("spec")
    fl.add_argument("--runs", type=int, default=5000)
    fl.add_argument("-o", "--out")
    dm = sub.add_parser("dmn", help="verifica una tabla DMN (JSON): solapes (hit U) y huecos (completitud C)")
    dm.add_argument("table")
    a = ap.parse_args()

    if a.cmd == "build":
        if a.help_spec or not a.spec:
            print(SPEC_HELP)
            return 0
        spec = load_spec(a.spec)
        errors, warnings, info = validate(graph_from_spec(spec))
        if errors and a.strict:
            report(errors, warnings, info)
            print("\n--strict: no se escribió el .bpmn (corrige los errores)")
            return 1
        xml = build_xml(spec)
        ET.fromstring(xml.encode("utf-8"))  # well-formedness
        out = a.out or re.sub(r"\.json$", "", a.spec) + ".bpmn"
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(xml)
        print(f"BPMN escrito: {out}")
        report(errors, warnings, info)
        return 1 if errors else 0
    if a.cmd == "validate":
        g = graph_from_spec(load_spec(a.model)) if a.model.endswith(".json") else graph_from_xml(a.model)
        errors, warnings, info = validate(g)
        report(errors, warnings, info)
        return 1 if errors else 0
    if a.cmd == "viewer":
        make_viewer(a.models, a.out, a.title)
        print(f"Visor escrito: {a.out}")
        return 0
    if a.cmd == "flow":
        txt = flow_report(load_spec(a.spec), a.runs)
        if a.out:
            with open(a.out, "w", encoding="utf-8") as fh:
                fh.write(txt)
            print(f"Informe escrito: {a.out}")
        else:
            print(txt)
        return 0
    if a.cmd == "dmn":
        with open(a.table, encoding="utf-8") as fh:
            tables = json.load(fh)
        bad = False
        for t in (tables if isinstance(tables, list) else [tables]):
            txt, b2 = dmn_check(t)
            bad |= b2
            print(txt + "\n")
        return 1 if bad else 0
    if a.cmd == "eventlog":
        txt = eventlog_report(a.log, a.case, a.activity, a.timestamp, a.resource, a.delimiter, a.top, a.mermaid,
                              a.start)
        if a.out:
            with open(a.out, "w", encoding="utf-8") as fh:
                fh.write(txt)
            print(f"Informe escrito: {a.out}")
        else:
            print(txt)
        return 0


def report(errors, warnings, info):
    print(f"\nVALIDACIÓN: {len(errors)} error(es), {len(warnings)} advertencia(s)")
    for e in errors:
        print("  ✗", e)
    for w in warnings:
        print("  ⚠", w)
    for i in info:
        print("  ·", i)
    if not errors:
        print("  ✓ Estructura y soundness correctas" + (" (revisa advertencias)" if warnings else ""))


if __name__ == "__main__":
    sys.exit(main())
