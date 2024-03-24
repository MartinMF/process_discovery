import itertools
import json
import re
import subprocess
import time
from typing import List, Dict

import requests as requests

from app.InduciveMinerLifeCycle import Activity, InductiveMinerLifeCycle
from app.PetriNetIMLC import PetriNetIMLC


def get_digraph_from_custom_petri_net(petri_net):
    penwidth = 1
    places = "\n".join([
        f'\t\t"{id(p)}" [label=<<B>{p.name[0] + "<SUB>" + p.name[1:] + "</SUB>"}</B>>, class="place", penwidth={penwidth+2}];' if \
            p.name in ["P0", "P1"] else \
            f'\t\t"{id(p)}" [label=<<B>{p.name[0] + "<SUB>" + p.name[1:] + "</SUB>"}</B>>, class="place", penwidth={penwidth}];'
        for p in petri_net.places])
    transitions = "\n".join([
        f'\t\t"{id(t)}" [label=<<B>{t.label}</B>>, name="{t.name}", class="transition", penwidth={penwidth}];' if \
            t.name != "τ" else \
            f'\t\t"{id(t)}" [label="", name="", class="transition", width=0.01, penwidth={penwidth}];'
        for t in petri_net.transitions])
    arcs = "\n".join([f'\t"{id(a.source)}"->"{id(a.target)}" [penwidth={penwidth}];' for a in petri_net.arcs])

    digraph = """digraph G {
\trankdir=LR;
\tcenter=true; margin=1;
\tsubgraph place {
\t\tnode [shape=circle,fixedsize=true,label="", height=.4,width=.4, fontsize="12pt"];
""" + places + """
\t}
\tsubgraph transitions {
\t\tnode [shape=rect,fixedsize=true,height=.6,width=.4, fontsize="12pt"];
""" + transitions + """
\t}
""" + arcs + """
}"""
    digraph = digraph.replace("source", "s0").replace("sink", "sf")
    digraph = re.sub(r'p_(\d+)', r'p\1', digraph)
    digraph = re.sub(r'None', r'tau', digraph)

    # print(digraph)
    return digraph


def get_digraph_from_json_log(process_name):
    traces = get_traces_from_log(process_name)
    traces = [list(trace.values())[0] for trace in traces]
    # print(traces)
    miner = InductiveMinerLifeCycle(traces)
    # print(miner.log)
    miner.find_sublogs_cuts(True)  # Set True to see when which cut was made
    print(f"Process Tree: {miner.process_tree}")
    petri_net = PetriNetIMLC(miner)
    # print(petri_net)
    digraph = get_digraph_from_custom_petri_net(petri_net)
    return digraph


def get_traces_from_json_log(process_name):
    traces = get_traces_from_log(process_name)
    traces_string = "\n".join(
        [f"{list(trace.keys())[0]}: {';'.join([a.html_name_str() for a in list(trace.values())[0]])}" for trace in
         traces])
    # print(traces_string)
    return traces_string


def get_traces_from_log(process_name) -> List[Dict[str, List[Activity]]]:
    logs = []
    with open("log.txt", 'r') as file:
        for line in file:
            log_entry = json.loads(line.strip())
            if log_entry["instance_name"] == process_name:
                logs.append(log_entry)

    try:
        logs = sorted(logs, key=lambda e: e["instance"])  # sort by instance
        logs = itertools.groupby(logs, lambda e: e["instance"])
    except Exception as e:
        print(e)
    try:
        logs = {key: sorted(list(value), key=lambda e: e["timestamp"]) for key, value in logs}
    except Exception as e:
        print(e)
    # print(logs)

    traces = []
    for instance, log_entries in logs.items():
        trace = {instance: []}
        for log_entry in log_entries:
            if log_entry["event"] == "calling":
                trace[instance] += [Activity(log_entry["activity"], "s", log_entry["label"])]
            if log_entry["event"] == "done":
                trace[instance] += [Activity(log_entry["activity"], "c", log_entry["label"])]
        traces += [trace]

    return traces


def convert_keys_to_int(data):
    if isinstance(data, dict):
        for key, value in list(data.items()):
            if (not isinstance(key, int)) and re.compile(r"^\d+$").match(key):
                data[int(key)] = value
                del data[key]
            convert_keys_to_int(value)
    elif isinstance(data, list):
        for item in data:
            convert_keys_to_int(item)


# log.txt -> activity_data.json
def update_activity_data():
    log_path = "log.txt"
    json_path = "activity_data.json"
    # log_path = "../log.txt"
    # json_path = "../activity_data.json"
    with open(log_path, "r") as f:
        lines = [json.loads(line) for line in f.readlines()]

    try:
        with open(json_path, "r") as json_file:
            data = json.load(json_file)
    except Exception as e:
        data = {}

    convert_keys_to_int(data)

    for log_entry in lines:
        process_name = log_entry["instance_name"]
        instance = int(log_entry["instance"])
        timestamp = log_entry["timestamp"]
        activity = log_entry["activity"]
        event_type = log_entry["event"]
        if process_name not in data.keys():
            data[process_name] = {
                activity: {
                    "instances": [instance],
                    "timestamps": {instance: [timestamp]},
                    "event_types": {instance: {timestamp: event_type}},
                    "name": log_entry["label"]
                }
            }
        else:
            process = data[process_name]
            if activity not in process.keys():
                process[activity] = {
                    "instances": [instance],
                    "timestamps": {instance: [timestamp]},
                    "event_types": {instance: {timestamp: event_type}},
                    "name": log_entry["label"]
                }
            else:
                logged_instances = process[activity]["instances"]
                if instance in logged_instances:
                    process[activity]["instances"] = logged_instances
                    process[activity]["timestamps"][instance] += [
                        timestamp] if timestamp not in process[activity]["timestamps"][instance] else []
                    process[activity]["event_types"][instance][timestamp] = event_type

                else:
                    process[activity]["instances"] = logged_instances + [instance]
                    process[activity]["timestamps"][instance] = [timestamp]
                    process[activity]["event_types"][instance] = {timestamp: event_type}

    convert_keys_to_int(data)

    with open(json_path, "w") as f:
        json.dump(data, f)

    return data


def start_process_instances(process_name, amount):
    for _ in range(amount):
        subprocess.run(['curl', '-X', 'POST', 'https://cpee.org/flow/start/xml/', '-F',
                        'behavior=fork_running', '-F', f'xml=@"processes/{process_name}.xml"'])


def get_log_txt_from_server():
    url = "https://lehre.bpm.in.tum.de/~ge93yoh/pd/log.txt"
    response = requests.get(url)
    if response.status_code == 200:
        log_text = response.text
        with open("log.txt", "w") as f:
            f.write(log_text)
        return log_text
    else:
        print("Failed to retrieve the log file:", response.status_code)
        return "DO NOT UPDATE"


def clear_log_txt():
    url = "https://lehre.bpm.in.tum.de/~ge93yoh/pd/clear_log.php"
    requests.get(url)
    with open("log.txt", "w") as f:
        f.write("")


def clear_activity_data_json():
    with open("activity_data.json", "w") as f:
        f.write("")


def count_lines(text):
    if text is None: return 0
    return text.count('\n') + 1


def monitor_remote_file():
    last_content = None

    while True:
        try:
            current_content = get_log_txt_from_server()
            current_lines = count_lines(current_content)
            last_lines = count_lines(last_content)

            if current_lines != last_lines:
                yield f"data: {current_lines - last_lines}\n\n"
                last_content = current_content

        except Exception as e:
            print(f"Error fetching remote file: {e}")

        time.sleep(.1)  # Timeout because of lehre.bpm.in.tum.de limit: "Max retries exceeded with url: log.txt [...]"
        # Error fetching remote file: HTTPSConnectionPool(host='lehre.bpm.in.tum.de', port=443): Max retries exceeded
        # with url: /~ge93yoh/pd/log.txt (Caused by NewConnectionError('<urllib3.connection.HTTPSConnection object at
        # 0x0000023D9D244490>: Failed to establish a new connection: [WinError 10048] Only one usage of each socket
        # address (protocol/network address/port) is normally permitted'))


if __name__ == "__main__":
    # update_activity_data()
    import os
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
    os.chdir(parent_dir)
    dg = get_digraph_from_json_log("Coopis 2010")
    print(dg)
