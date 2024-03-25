import functools
import itertools
from collections import defaultdict
from enum import Enum
from typing import List, Tuple, Set


class CutType(Enum):
    SEQUENCE = "→"
    EXCLUSIVE = "×"
    PARALLEL = "+"  # ∧
    LOOP = "◯"
    INTERLEAVING = "<->"
    # MAYBE_INTERLEAVING = "<?>"
    UNKNOWN = "?"
    MINIMAL = ""


class Activity:
    def __init__(self, label: str, event_type: str = "d", name=None):
        self.label = label  # acts as ID
        self.event_type = event_type  # s: start or c: complete / d: default for collapsed
        self.name = name if name else label

    def __eq__(self, other):
        return self.label == other.label and self.event_type == other.event_type

    def __hash__(self):
        return hash((self.label, self.event_type))  # Hash based on label and event_type

    def __repr__(self):
        return f"{self.label}_{self.event_type}" if self.event_type != "d" else self.label

    def __str__(self):
        return f"{self.label}_{self.event_type}" if self.event_type != "d" else self.label

    def html_name_str(self):
        return f"{self.name}<sub>{self.event_type}</sub>" if self.event_type != "d" else self.name

    def get_default(self):
        return Activity(self.label, "d", self.name)

    def get_start(self):
        return Activity(self.label, "s", self.name)

    def get_complete(self):
        return Activity(self.label, "c", self.name)


def find_item(element, array):
    for i in range(len(array)):
        if element in array[i]:
            return array[i]


def all_equal(iterable):
    g = itertools.groupby(iterable)
    return next(g, True) and not next(g, False)


def get_collapsed_activities(traces: List[List[Activity]]) -> List[Activity]:
    activities = []
    candidates = []
    for expanded_activity in sum(traces, []):
        activity = expanded_activity.get_default()
        if expanded_activity.event_type == "s":
            candidates += [activity]
        elif expanded_activity.event_type == "c":
            if activity in candidates:
                activities += [activity]
                candidates.remove(activity)
    all_activities = activities + candidates
    return list(set(all_activities))


def get_dfg_from_expanded_traces(traces: List[List[Activity]]) -> List[Tuple[Activity]]:
    dfg = []
    for trace in traces:
        current_events = []  # tracker of which events are currently started but not completed
        for i in range(len(trace) - 1):
            label = trace[i].label
            event_type = trace[i].event_type
            source_activity = trace[i].get_default()
            if event_type == "s":
                current_events += [source_activity]
                end_activity = trace[i].get_complete()
                end_index = i + 1 if end_activity not in trace else trace.index(end_activity)
                for j in range(i + 1, end_index):
                    target_activity = trace[j].get_default()
                    dfr = (source_activity, target_activity)
                    if not any([gdfr[0].label == dfr[0].label and gdfr[1].label == dfr[1].label for gdfr in dfg]):
                        dfg += [dfr]
                    if is_complete_activity_in_trace(target_activity, trace[i:end_index]):
                        dfr = (target_activity, source_activity)
                        if not any([gdfr[0].label == dfr[0].label and gdfr[1].label == dfr[1].label for gdfr in dfg]):
                            dfg += [dfr]

            elif event_type == "c":
                target_activity = trace[i].get_default()
                if target_activity not in current_events:
                    # print(f"{target_activity} completed but not started")
                    pass
                else:
                    current_events.remove(target_activity)
                started = []
                for j in range(i + 1, len(trace)):
                    current_label = trace[j].label
                    current_event_type = trace[j].event_type
                    # print(f"current_activity: {trace[i]} - {trace[j]}")
                    if current_event_type == "s":
                        dfr = (trace[i].get_default(), trace[j].get_default())
                        # print(f"(2) Adding {label} -> {current_label}")
                        if not any([gdfr[0].label == dfr[0].label and gdfr[1].label == dfr[1].label for gdfr in dfg]):
                            dfg += [dfr]
                        started += current_label
                    if current_event_type == "c":
                        dfr = (trace[i].get_default(), trace[j].get_default())
                        # print(f"Adding {label} -> {current_label}")
                        if not any([gdfr[0].label == dfr[0].label and gdfr[1].label == dfr[1].label for gdfr in dfg]):
                            pass  # dfg += [dfr]
                        if current_label in started:
                            started = []
                            # print(f"Breaking {trace[i]} and {trace[j]}")
                            break
    return dfg


def get_ccg_from_expanded_traces(traces: List[List[Activity]]) -> List[Set[Activity]]:
    def overlap(a: Activity, b: Activity, trace: List[Activity]) -> bool:
        start_activity, end_activity = a.get_start(), a.get_complete()
        if start_activity not in trace: return False  # if only completion event exists, then it is atomic
        i = trace.index(start_activity)
        # Using Life Cycle Information in Process Discovery:
        # "completion events are inserted right after unmatched start events" -> j = i+1
        j = i + 1 if end_activity not in trace else trace.index(end_activity)
        for activity in trace[i + 1:j]:
            if b.label == activity.label:
                return True
        return False

    def ccg_has_edge(ccg: List[Set[Activity]], a: Activity, b: Activity) -> bool:
        for edge in ccg:
            if a in edge and b in edge:
                return True
        return False

    ccg = []
    for trace in traces:
        for i, a in enumerate(trace):
            for j, b in enumerate(trace):
                if i != j and (overlap(a, b, trace) or overlap(b, a, trace)):
                    a = a.get_default()
                    b = b.get_default()
                    if not ccg_has_edge(ccg, a, b):
                        ccg.append({a, b})
    # print(f"CCG: {ccg}")
    return ccg


def reaches(a: Activity, b: Activity, dfg: List[Tuple[Activity]]) -> bool:
    visited = set()

    def dfs(activity: Activity) -> bool:
        if activity == b:
            return True
        visited.add(activity)
        for next_activity in [act for act in dfg if act[0] == activity]:
            if next_activity[1] not in visited and dfs(next_activity[1]):
                return True
        return False

    return dfs(a)


def directly_reaches(a: Activity, b: Activity, dfg: List[Tuple[Activity]]) -> bool:
    return (a, b) in dfg


def is_concurrent(a: Activity, b: Activity, ccg: List[Set[Activity]]) -> bool:
    return {a.get_default(), b.get_default()} in ccg


def are_concurrent(pa: Set[Activity], pb: Set[Activity], ccg: List[Set[Activity]]) -> bool:
    concurrent = True
    for a in pa:
        for b in pb:
            if not is_concurrent(a, b, ccg):
                concurrent = False
    return concurrent


def get_tau_activities():
    return [Activity("τ", "s"), Activity("τ", "c")]


def get_default_tau_activity():
    return Activity("τ")


def create_sublogs(traces, partitions):
    grouped_traces = []
    for trace in traces:
        grouped_trace = [[] for _ in range(len(partitions))]
        for event in trace:
            for i, s in enumerate(partitions):
                if event.get_default() in s:
                    grouped_trace[i].append(event)
                    break
        grouped_traces.append(grouped_trace)
    transposed = list(map(list, zip(*grouped_traces)))
    with_taus = [[get_tau_activities() if not a else a for a in trace] for trace in transposed]
    return with_taus


def create_loop_sublogs_old_2(traces, partitions):
    loop_sublogs = [[] for _ in partitions]
    # print(f"Trying to loop cut: {traces}, p = {partitions}")
    for trace in traces:
        latest_sub_log_index = None
        current_sub_trace = []
        for a in trace:
            # print(f"Activitiy: {a}")
            current_sub_log_index = partitions.index(find_item(a.get_default(), partitions))
            if latest_sub_log_index is None:
                latest_sub_log_index = current_sub_log_index
            if latest_sub_log_index == current_sub_log_index:
                current_sub_trace += [a]
            else:
                # print(f"Change in partition: {a}, {current_sub_trace}")
                loop_sublogs[latest_sub_log_index] += [current_sub_trace]
                current_sub_trace = []
                latest_sub_log_index = current_sub_log_index

    return loop_sublogs


def create_loop_sublogs(traces, partitions):
    new_log = [[], []]  # do part, redo part
    for trace in traces:
        current_subtrace = []
        current_partition = None
        current_pi = None

        for activity in trace:
            activity_partition = None
            act_pi = None
            for i, part in enumerate(partitions):
                if activity.get_default() in part:
                    activity_partition = part
                    act_pi = i
                    break

            if current_partition is not None and activity_partition != current_partition:
                # print(f"Appending {current_subtrace} to PI: {current_pi}")
                new_log[current_pi].append(current_subtrace)
                current_subtrace = []

            current_subtrace.append(activity)
            current_partition = activity_partition
            current_pi = act_pi

        # print(f"Appending {current_subtrace} to PI: {current_pi}")
        new_log[current_pi].append(current_subtrace)

    return new_log


def remove_taus_sub_logs(sub_logs, p):
    ps = len(p)
    for traces in sub_logs:
        removed = 0
        while get_tau_activities() in traces and removed < ps:
            traces.remove(get_tau_activities())
            removed += 1
    return sub_logs


def remove_all_taus_sub_logs(sub_logs):
    for traces in sub_logs:
        while get_tau_activities() in traces:
            traces.remove(get_tau_activities())
    return sub_logs


def merge_sets(set_list, merge_instructions):
    merged_set_list = []
    merged = set()

    for merge_instruction in merge_instructions:
        merged_set = set()
        for element in merge_instruction:
            for s in set_list:
                if element in s:
                    merged_set |= s
                    merged |= {set_list.index(s)}
                    break
        merged_set_list.append(merged_set)

    for i, s in enumerate(set_list):
        if i not in merged:
            merged_set_list.append(s)

    return merged_set_list


def collapsed_tau_traces_partitions(transposed_traces, partitions):
    collapsed_traces = []
    tau_s, tau_c = get_tau_activities()
    collapsed_activities = []
    for j, trace in enumerate(transposed_traces):
        collapsed_partition = set()
        collapsed_trace = []
        started_tau, completed_tau = False, False
        for i, a in enumerate(trace):
            if a in [tau_s, tau_c]:
                if a == tau_s:
                    if not started_tau:
                        started_tau = True
                        collapsed_trace += [a]
                    else:
                        pass  # do not add it
                else:  # a == tau_c
                    if not completed_tau:
                        completed_tau = True
                        collapsed_trace += [a]
                    else:
                        pass  # do not add it

                activities = set(sum([[act.get_default() for x, act in enumerate(trace) if
                                       (x == i and act.get_default() != get_default_tau_activity())] for y, trace in
                                      enumerate(transposed_traces)], []))
                collapsed_partition |= activities
            else:
                collapsed_trace += [a]
                if len(collapsed_partition) and collapsed_partition not in collapsed_activities:
                    collapsed_activities += [collapsed_partition]
                collapsed_partition = set()
                started_tau, completed_tau = False, False

        collapsed_traces += [collapsed_trace]
    return collapsed_traces, merge_sets(partitions, collapsed_activities)


def get_start_end_activities_from_trace(trace: List[Activity]) -> Tuple[List[Activity], List[Activity]]:
    starts = []
    for a in trace:
        if a.event_type == "c":
            break
        activity = a.get_default()
        if activity not in starts:
            starts += [activity]
    ends = []
    for a in trace[::-1]:
        if a.event_type == "s":
            break
        activity = a.get_default()
        if activity not in starts:
            ends += [activity]
    return starts, ends


def get_start_end_activities_from_traces(traces: List[List[Activity]]) -> Tuple[Set[Activity], Set[Activity]]:
    start_activities = []
    end_activities = []
    for trace in traces:
        start, end = get_start_end_activities_from_trace(trace)
        start_activities.append(start)
        end_activities.append(end)
    common_start_activities = set.intersection(*map(set, start_activities))
    common_end_activities = set.intersection(*map(set, end_activities))
    return common_start_activities, common_end_activities


def concurrent_start_end_activities(traces, p, root_dfg) -> bool:
    outside_activities = set(get_collapsed_activities(traces)) - set().union(*p)
    start_activities = sum(
        [[set([target for source, target in root_dfg if target.label == a.label]) for a in part] for part in p], [])
    end_activities = sum(
        [[set([source for source, target in root_dfg if source.label == a.label]) for a in part] for part in p], [])
    start_sources = sum(
        [[set([source for source, target in root_dfg if target.label == a.label]) & outside_activities for a in part]
         for part in p], [])
    end_targets = sum(
        [[set([target for source, target in root_dfg if source.label == a.label]) & outside_activities for a in part]
         for part in p], [])
    root_starts, root_ends = get_start_end_activities_from_traces(traces)

    # print(p, start_activities, end_activities, start_sources, end_targets, root_starts, root_ends)

    if set() in start_activities or set() in end_activities:
        return False

    # all outside activities that connect into a partition (ss),
    # connect to all start activities of this partition (sa)
    for i, part in enumerate(p):
        ss = start_sources[i]
        sa = start_activities[i]
        for source in ss:
            for target in sa:
                if not directly_reaches(source, target, root_dfg):
                    return False

    # all outside connections that connect to a partition as above,
    # it must do so for all partitions in p
    if not all_equal(start_sources):
        return False

    # ea -> et
    for i, part in enumerate(p):
        ea = end_activities[i]
        et = end_targets[i]
        for source in ea:
            for target in et:
                if not directly_reaches(source, target, root_dfg):
                    return False

    if not all_equal(end_targets):
        return False

    # iff a partition has root start activities,
    # all start activities of all partitions must be root start activities
    if list(start_activities[0])[0] in root_starts:
        for i, part in enumerate(p):
            sa = start_activities[i]
            if sa != root_starts:
                # print(f"{sa} != {root_starts}")
                return False
    else:
        for i, part in enumerate(p):
            sa = start_activities[i]
            if len(list(sa & root_starts)) > 0:
                # print(f"Any {sa} in {root_starts}")
                return False

    # same for root end activities:
    if list(start_activities[0])[0] in root_ends:
        for i, part in enumerate(p):
            ea = end_activities[i]
            if ea != root_ends:
                # print(f"{ea} != {root_ends}")
                return False
    else:
        for i, part in enumerate(p):
            ea = end_activities[i]
            if len(list(ea & root_ends)) > 0:
                # print(f"Any {ea} in {root_ends}")
                return False

    # print(concurrent)
    return True


def is_complete_activity_in_trace(a: Activity, trace: List[Activity]) -> bool:
    start, end = False, False
    for act in trace:
        if act.label == a.label:
            if act.event_type == "s":
                start = True
            if act.event_type == "c":
                end = True
        if start and end:
            return True
    return start and end


def remove_latest_element(activity: Activity, input_list: List[Tuple[Activity, int]]):
    for i in range(len(input_list) - 1, -1, -1):
        if input_list[i][0] == activity:
            del input_list[i]
            break


def correct_incomplete_traces(traces: List[List[Activity]]) -> List[List[Activity]]:
    # Incomplete events are handled as atomic events.
    corrected_traces = []
    original_traces = [[a for a in t] for t in traces]

    for i, trace in enumerate(original_traces):
        corrected_trace = []
        active_activities = []
        added_activities = 0

        for j, activity in enumerate(trace):
            if activity.event_type == "s":
                active_activities += [(activity.get_default(), j + added_activities)]
            elif activity.event_type == "c":
                if activity.get_default() not in [a for a, _ in active_activities]:
                    corrected_trace += [activity.get_start()]
                    added_activities += 1
                else:
                    remove_latest_element(activity.get_default(), active_activities)
            corrected_trace += [activity]

        j = 0
        for a, k in active_activities:
            corrected_trace.insert(k + (j := j + 1), a.get_complete())

        corrected_traces += [corrected_trace]
    return corrected_traces


class InductiveMinerLifeCycle:
    def __init__(self, traces, root_dfg=None):
        traces = correct_incomplete_traces(traces)
        self.dfg = get_dfg_from_expanded_traces(traces)
        self.root_dfg = root_dfg if root_dfg else get_dfg_from_expanded_traces(traces)
        self.ccg = get_ccg_from_expanded_traces(traces)
        self.activities = get_collapsed_activities(traces)

        self.log = traces
        self.cut_type = CutType.UNKNOWN

        self.apply_base_case()
        self.built_process_tree = False
        self.debug = False

    @property
    def process_tree(self):
        if self.cut_type == CutType.MINIMAL:
            return "" + "τ" if not len(self.activities) else str(self.activities[0].get_default()) + ""
        if not self.built_process_tree: return "[!] No process tree available. Use find_sublog_cuts first."
        try:
            return self.cut_type.value + "(" + ",".join([m.process_tree for m in self.log]) + ")"
        except:
            return "[!] No Process Tree available."

    def find_sublogs_cuts(self, debug=False):
        self.debug = debug
        # print(f"Finding Cuts for: {self.log}")
        if self.cut_type != CutType.UNKNOWN:
            self.built_process_tree = True
            return
        cut_type = CutType.UNKNOWN
        sub_logs, cut_partition = None, None
        if self.cut_type == CutType.UNKNOWN:
            sub_logs, cut_partition, cut_type = self.find_sequence_cuts()
        if cut_type == CutType.UNKNOWN:
            sub_logs, cut_partition, cut_type = self.find_interleaved_cuts()
            if cut_type == CutType.INTERLEAVING:
                if self.debug:
                    print(f"[+] Sublogs: {sub_logs}, Partitions: {cut_partition}, CutType: {cut_type} -> ", end="")
                self.cut_type = cut_type
                if self.debug:
                    print(f"{self.cut_type.value}{cut_partition}")
                self.log = [InductiveMinerLifeCycle([[a.get_start(), a.get_complete()]]) for a in self.activities]
                for imlc in self.log: imlc.find_sublogs_cuts(self.debug)
                self.built_process_tree = True
                return
        if cut_type == CutType.UNKNOWN:
            sub_logs, cut_partition, cut_type = self.find_parallel_cuts()
        if cut_type == CutType.UNKNOWN:
            sub_logs, cut_partition, cut_type = self.find_exclusive_cuts()
        if cut_type == CutType.UNKNOWN:
            sub_logs, cut_partition, cut_type = self.find_loop_cut()
        if cut_type == CutType.UNKNOWN:
            self.assign_fall_through()
            self.built_process_tree = True
            return
        if self.debug:
            print(f"[+] Sublogs: {sub_logs}, Partitions: {cut_partition}, CutType: {cut_type} -> ", end="")
        self.cut_type = cut_type
        if self.debug:
            print(f"{self.cut_type.value}{cut_partition}")
            # print(f"[!] {self.log} -> {sub_logs}")

        new_imlcs = [InductiveMinerLifeCycle(log, self.root_dfg) for log in sub_logs]

        self.log = new_imlcs

        for imlc in new_imlcs:
            imlc.find_sublogs_cuts(self.debug)

        self.built_process_tree = True
        return self.log

    def find_sequence_cuts(self):
        if len(self.dfg) == 0:
            return None, None, CutType.UNKNOWN
        p = [{n} for n in self.activities]

        for a in self.activities:
            for b in self.activities:
                if reaches(a, b, self.dfg) and reaches(b, a, self.dfg):  # and a != b:
                    # print(f"No sequence cut - pairwise reachable: {a}, {b}")
                    pa = find_item(a, p)
                    pb = find_item(b, p)
                    if pa != pb:
                        p.remove(pa)
                        p.remove(pb)
                        p.append(pa | pb)

                if not reaches(a, b, self.dfg) and not reaches(b, a, self.dfg):  # and a != b:
                    # print(f"No sequence cut: {a}, {b}")
                    pa = find_item(a, p)
                    pb = find_item(b, p)
                    if pa != pb:
                        p.remove(pa)
                        p.remove(pb)
                        p.append(pa | pb)

        if len(p) == 1:
            return None, None, CutType.UNKNOWN

        # sort for reachability
        def reachability_sort(pa, pb):
            if all(reaches(a, b, self.dfg) for a in pa for b in pb):
                return -1  # pa < pb: pa -> pb
            else:
                return 1  # pa >= pb

        p = sorted(p, key=functools.cmp_to_key(reachability_sort))

        # In sublogs with traces with > 1 consecutive taus, these will be merged, partitions respectively
        sub_logs = create_sublogs(self.log, p)

        transposed_logs = [sum(list(trace), []) for trace in list(zip(*sub_logs))]  # old traces
        collapsed_traces, new_partitions = collapsed_tau_traces_partitions(transposed_logs, p)
        p = sorted(new_partitions, key=functools.cmp_to_key(reachability_sort))
        sub_logs = create_sublogs(collapsed_traces, p)

        p = sorted(new_partitions, key=functools.cmp_to_key(reachability_sort))
        return sub_logs, p, CutType.SEQUENCE

    def find_maybe_interleaved_cuts(self):
        p = [{n} for n in self.activities]
        for a in self.activities:
            for b in self.activities:
                if is_concurrent(a, b, self.ccg):  # and a != b:
                    pa = find_item(a, p)
                    pb = find_item(b, p)
                    if pa != pb:
                        p.remove(pa)
                        p.remove(pb)
                        p.append(pa | pb)
                # print(f"Did not join {a} and {b} because {a}->{b}: {reaches(a,b,self.dfg)}; {b}->{a}: {reaches(a,b,self.dfg)}\nDFG: {self.dfg}")
        # if not reaches(a, b, self.dfg) or not reaches(b, a, self.dfg):
        if len(p) == 1:
            return None, None, CutType.UNKNOWN

    def find_interleaved_cuts(self):
        p = [{n} for n in self.activities]
        np = [{n} for n in self.activities]
        for a in self.activities:
            for b in self.activities:
                if not directly_reaches(a, b, self.dfg) or not directly_reaches(b, a, self.dfg):  # and a != b:
                    # if not is_concurrent(a, b, self.ccg):  # and a != b:
                    pa = find_item(a, p)
                    pb = find_item(b, p)
                    if pa != pb:
                        p.remove(pa)
                        p.remove(pb)
                        p.append(pa | pb)

        # Check for same start and end activities
        concurrent_start_end_activities(self.log, p, self.root_dfg)
        if not concurrent_start_end_activities(self.log, p, self.root_dfg):
            return None, None, CutType.UNKNOWN

        concurrent = True
        for pa in p:
            for pb in [s for s in p if s != pa]:
                if not are_concurrent(pa, pb, self.ccg):
                    concurrent = False

        if not concurrent:
            for a in self.activities:
                for b in self.activities:
                    # if not reaches(a, b, self.dfg) or not reaches(b, a, self.dfg):  # and a != b:
                    if not is_concurrent(a, b, self.ccg):  # and a != b:
                        npa = find_item(a, np)
                        npb = find_item(b, np)
                        if npa != npb:
                            np.remove(npa)
                            np.remove(npb)
                            np.append(npa | npb)

            if len(np) > 1:
                p = np
                concurrent = True

        # print(f"Interleaved/concurrent? p: {p}")
        if len(p) == 1:
            return None, None, CutType.UNKNOWN

        sub_logs = create_sublogs(self.log, p)
        # print(f"Created logs: {sub_logs}")
        return sub_logs, p, CutType.INTERLEAVING if not concurrent else CutType.PARALLEL

    def find_parallel_cuts(self):
        p = [{n} for n in self.activities]
        for a in self.activities:
            for b in self.activities:
                # if not reaches(a, b, self.dfg) or not reaches(b, a, self.dfg):  # and a != b:
                if not is_concurrent(a, b, self.ccg):  # and a != b:
                    pa = find_item(a, p)
                    pb = find_item(b, p)
                    if pa != pb:
                        p.remove(pa)
                        p.remove(pb)
                        p.append(pa | pb)

        if len(p) == 1:
            return None, None, CutType.UNKNOWN

        sub_logs = create_sublogs(self.log, p)
        sub_logs = remove_taus_sub_logs(sub_logs, p)
        return sub_logs, p, CutType.PARALLEL

    def find_exclusive_cuts(self):
        p = [{n} for n in self.activities]
        for a in self.activities:
            for b in self.activities:
                if reaches(a, b, self.dfg) or reaches(b, a, self.dfg):  # and a != b:
                    pa = find_item(a, p)
                    pb = find_item(b, p)
                    if pa != pb:
                        p.remove(pa)
                        p.remove(pb)
                        p.append(pa | pb)

        if len(p) == 1:
            return None, None, CutType.UNKNOWN

        sub_logs = create_sublogs(self.log, p)
        sub_logs = remove_all_taus_sub_logs(sub_logs)
        return sub_logs, p, CutType.EXCLUSIVE

    def find_loop_cut(self):
        start_activities, end_activities = get_start_end_activities_from_traces(self.log)
        do_set = set(start_activities) | set(end_activities)  # Start do_set with start/end activities
        redo_set = set(self.activities) - do_set

        # move nodes from redo set to do set if they violate any loop cut conditions
        # If ∃x->a <=> ∃b->a AND if b->∃a <=> ∃x->a
        for b in redo_set:
            if any([directly_reaches(a, b, self.dfg) and a not in end_activities or \
                    directly_reaches(b, a, self.dfg) and a not in start_activities for a in do_set]):
                do_set -= {b}
                redo_set |= {b}

        if len(do_set) > 0 and len(redo_set) > 0:
            p = [do_set, redo_set]
            new_loop_logs = create_loop_sublogs(self.log, p)
            return new_loop_logs, p, CutType.LOOP
        return None, None, CutType.UNKNOWN

    def assign_fall_through(self):
        if self.debug:
            print(
                f"[-] Applying fallthrough for log: {self.log} - {'empty_trace' if get_tau_activities() in self.log else 'flower_model'}")

        def empty_trace():
            new_traces = [[get_tau_activities()],
                          [trace for trace in self.log if trace != get_tau_activities()]]
            tau_imlc = InductiveMinerLifeCycle(new_traces[0], self.root_dfg)
            non_tau_imlc = InductiveMinerLifeCycle(new_traces[1], self.root_dfg)
            self.cut_type = CutType.EXCLUSIVE
            self.log = [tau_imlc, non_tau_imlc]
            for imlc in self.log:
                imlc.find_sublogs_cuts()

        def flower_model():
            new_traces = [[get_tau_activities()], [[a.get_start(), a.get_complete()] for a in self.activities]]
            tau_imlc = InductiveMinerLifeCycle(new_traces[0], self.root_dfg)
            exclusive_imlc = InductiveMinerLifeCycle(new_traces[1], self.root_dfg)
            self.cut_type = CutType.LOOP
            self.log = [exclusive_imlc, tau_imlc]
            for imlc in self.log:
                imlc.find_sublogs_cuts()

        def tau_flower():
            new_traces = [[get_tau_activities()], [[a.get_start(), a.get_complete()] for a in self.activities]]
            tau_imlc = InductiveMinerLifeCycle(new_traces[0], self.root_dfg)
            exclusive_imlc = InductiveMinerLifeCycle(new_traces[1], self.root_dfg)
            self.cut_type = CutType.LOOP
            self.log = [tau_imlc, exclusive_imlc]
            for imlc in self.log:
                imlc.find_sublogs_cuts()

        if get_tau_activities() in self.log:
            empty_trace()
        else:
            flower_model()

        # tau_flower()

    def apply_base_case(self):
        base_case = True
        activities = get_collapsed_activities(self.log)
        if not all_equal(activities): base_case = False
        for trace in self.log:
            if len(trace) <= 2:
                if len(trace) == 0:
                    pass
                elif len(trace) == 1 and trace[0].event_type == "s":
                    pass
                # elif trace[0].label == "τ": base_case = False
                elif trace[0].label == trace[1].label and trace[0].event_type == "s" and trace[1].event_type == "c":
                    pass
                else:
                    base_case = False
            else:
                base_case = False
        self.cut_type = CutType.MINIMAL if base_case else CutType.UNKNOWN


if __name__ == "__main__":
    a_s = Activity("a", "s")
    a_c = Activity("a", "c")
    b_s = Activity("b", "s")
    b_c = Activity("b", "c")
    c_s = Activity("c", "s")
    c_c = Activity("c", "c")
    d_s = Activity("d", "s")
    d_c = Activity("d", "c")
    e_s = Activity("e", "s")
    e_c = Activity("e", "c")
    f_s = Activity("f", "s")
    f_c = Activity("f", "c")
    g_s = Activity("g", "s")
    g_c = Activity("g", "c")
    h_s = Activity("h", "s")
    h_c = Activity("h", "c")

    i_s = Activity("i", "s")
    i_c = Activity("i", "c")
    m_s = Activity("m", "s")
    m_c = Activity("m", "c")
    x_s = Activity("x", "s")
    x_c = Activity("x", "c")
    l_s = Activity("l", "s")
    l_c = Activity("l", "c")

    # Examples:
    # traces = [[i_s, i_c, m_s, m_c, x_s, l_s, x_c, l_c, f_s, f_c], [i_s, i_c, l_s, x_s, x_c, m_s, l_c, m_c, f_s, f_c]]
    # traces = [[m_s, m_c, x_s, l_s, x_c, l_c], [l_s, x_s, x_c, m_s, l_c, m_c]]
    # traces = [[a_s, a_c, b_s, e_s, f_s, b_c, c_s, e_c, c_c, f_c, d_s, d_c]]
    # traces = [[a_s, a_c, b_s, e_s, b_c, f_s, c_s, e_c, c_c, f_c, d_s, d_c]]
    # traces = [[a_s, a_c, b_s, b_c, c_s, c_c, d_s, d_c], [a_s, a_c, d_s, d_c]]
    # traces = [[a_s, a_c, b_s, b_c, c_s, c_c], [a_s, a_c, c_s, c_c]]
    # traces = [[b_s, b_c], [a_s, a_c]]
    # traces = [[a_s, a_c, b_s, b_c, c_s, c_c, d_s, d_c], [a_s, a_c, c_s, c_c, b_s, b_c, d_s, d_c], [e_s, e_c, f_s, f_c, g_s, g_c, d_s, d_c], [e_s, e_c, g_s, g_c, f_s, f_c, d_s, d_c]]
    # traces = [[b_s, b_c, c_s, c_c], [c_s, c_c, b_s, b_c]]
    # traces = [[a_s, a_c, b_s, b_c, c_s, c_c, d_s, d_c], [a_s, a_c, e_s, e_c, d_s, d_c]]
    # traces = [[b_s, b_c, c_s, c_c], [e_s, e_c]]
    # traces = [[a_s, a_c, b_s, b_c], [b_s, b_c, a_s, a_c]]
    # traces = [[a_s, a_c, b_s, b_c, a_s, a_c]]
    # traces = [[a_s, a_c, b_s, b_c, c_s, c_c, a_s, a_c]]
    # traces = [[a_s, a_c, b_s, b_c, c_s, c_c, d_s, d_c, a_s, a_c, b_s, b_c]]
    # traces = [[a_s, a_c, b_s, b_c, c_s, c_c, d_s, d_c, a_s, a_c, b_s, b_c, c_s, c_c, d_s, d_c, a_s, a_c, b_s, b_c, b_s, b_c]]
    # traces = [[a_s, a_c, b_s, b_c, c_s, c_c, d_s, d_c, a_s, a_c, c_s, c_c, d_s, d_c, a_s, a_c, b_s, b_c]]
    # traces = [[a_s, a_c, b_s, b_c, c_s, c_c, e_s, e_c], [a_s, a_c, b_s, b_c, c_s, c_c, d_s, d_c, b_s, b_c, c_s, c_c, e_s, e_c]]
    # traces = [[a_s, a_s, a_c, a_c, b_s, b_c, c_c, c_s, d_s, d_c]]
    # traces = [[a_s, a_c, d_s, d_c, g_s, g_c], [a_s, a_c, b_s, b_c, c_s, c_c, d_s, d_c, e_s, e_c, f_s, f_c, g_s, g_c]]
    traces = [[a_s, a_c, b_s, b_c, c_s, c_c], [c_s, c_c, a_s, a_c, b_s, b_c]]

    miner = InductiveMinerLifeCycle(traces)
    cuts = miner.find_sublogs_cuts(True)
    print(miner.process_tree)
    print(miner.ccg)
    # print()
    print(miner.dfg)
    # print(miner.ccg)
