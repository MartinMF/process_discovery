from app.InduciveMinerLifeCycle import CutType, InductiveMinerLifeCycle


class Place:
    def __init__(self, name):
        self.name = name
        self.tokens = 0
        self.active = False

    def __repr__(self):
        return self.name

    def add_token(self):
        self.tokens += 1

    def remove_token(self):
        if self.tokens > 0:
            self.tokens -= 1


class Transition:
    def __init__(self, label, name=None):
        self.label = label  # id
        self.name = name if name else label

    def __repr__(self):
        return f"{self.label}_({self.name})"


class Arc:
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def set_source(self, source):
        self.source = source

    def set_target(self, target):
        self.target = target

    def __repr__(self):
        return f"{self.source} -> {self.target}"

    def __eq__(self, other):
        return self.source == other.source and self.target == other.target and type(self) == type(other)

    def __hash__(self):
        return hash((self.source, self.target))


class PetriNetIMLC:
    def __init__(self, imlc_miner=None):
        self.initial_place = Place(f"P0"); self.initial_place.active = True
        self.final_place = Place(f"P1")
        self.initial_transition = Transition("T0")
        self.places = [self.initial_place, self.final_place]
        self.transitions = {self.initial_transition}
        self.arcs = {Arc(self.initial_place, self.initial_transition), Arc(self.initial_transition, self.final_place)}
        if imlc_miner: self.create_from_imlc_miner(imlc_miner)

    def __repr__(self):
        return f"PetriNet:\n\tPlaces:\n\t\t{self.places}\n\tTransitions:\n\t\t{self.transitions}\n\tArcs:\n\t\t{self.arcs}\n"

    def add_new_place(self):
        new_place = Place(f"P{len(self.places)}")
        self.places += [new_place]
        return new_place

    def replace_transition(self, transition, petri_net):
        source_places = [a.source for a in self.arcs if a.target == transition]
        # print(f"Source places: {source_places}, Arcs: {self.arcs}, Transition: {transition}")
        target_places = [a.target for a in self.arcs if a.source == transition]
        sub_start_transitions = [a.target for a in petri_net.arcs if a.source == petri_net.places[0]]
        sub_end_transitions = [a.source for a in petri_net.arcs if a.target == petri_net.places[1]]

        # Remove (placeholder) transition
        # print(f"Replacing Transition: {transition} with {petri_net}")
        self.transitions.remove(transition)

        # Remove arcs that connected to removed transition
        new_arcs = set()
        for a in self.arcs:
            if transition not in [a.source, a.target]:
                new_arcs.add(a)
        self.arcs = new_arcs

        # Create Arcs from original PetriNet to new one
        for p in source_places:
            for t in sub_start_transitions:
                self.arcs.add(Arc(p, t))

        # Create Arcs from new PetriNet to original one
        for t in sub_end_transitions:
            for p in target_places:
                self.arcs.add(Arc(t, p))

        # Add Places from new PetriNet, excluding their initial start and final places
        if len(petri_net.places) > 2:
            for p in petri_net.places[2:]:
                self.places += [p]

        # Add Transitions from new PetriNet
        if len(petri_net.transitions) > 0:
            for t in petri_net.transitions:
                self.transitions.add(t)

        # Add Arcs from new PetriNet, excluding arcs from initial start place and to final place
        if len(petri_net.arcs) > 0:
            for a in petri_net.arcs:
                if a.source not in petri_net.places[:2] and a.target not in petri_net.places[:2]:
                    self.arcs.add(a)

        # Rename places
        for i in range(2, len(self.places)):
            self.places[i].name = f"P{i}"

    def create_from_imlc_miner(self, miner: InductiveMinerLifeCycle):
        # Create PetriNet with each process_subtree (log entry) being a PetriNet with a single placeholder transition
        # Build PetriNet based on base cases

        if miner.cut_type == CutType.MINIMAL:
            self.initial_transition.label = miner.process_tree
            if len(miner.activities) == 1:
                self.initial_transition.name = miner.activities[0].name
            elif len(miner.activities) == 0:
                self.initial_transition.name = miner.process_tree
            else:
                print(f"[-] Minimal Tree has > 1 activities")
            return

        sub_nets = [(Transition(sub_miner.process_tree), PetriNetIMLC(sub_miner)) for sub_miner in miner.log]
        # [print(Transition(sub_miner.process_tree)) for sub_miner in miner.log]

        self.transitions, self.arcs, self.initial_transition = set(), set(), None

        if miner.cut_type == CutType.SEQUENCE:
            # print(f"Applying sequence conversion")
            for i in range(len(sub_nets)-1):
                transitions = sub_nets[i][0], sub_nets[i+1][0]
                place = Place(f"P{len(self.places)}")
                arc_1 = Arc(transitions[0], place)
                arc_2 = Arc(place, transitions[1])
                self.places.append(place)
                self.arcs.add(arc_1)
                self.arcs.add(arc_2)
            self.arcs.add(Arc(self.initial_place, sub_nets[0][0]))
            self.arcs.add(Arc(sub_nets[-1][0], self.final_place))
            self.transitions = {t for t, _ in sub_nets}
            for trans, net in sub_nets:
                self.replace_transition(trans, net)

        elif miner.cut_type == CutType.EXCLUSIVE:
            # print(f"Applying exclusive conversion")
            for t, _ in sub_nets:
                arc_1 = Arc(self.initial_place, t)
                arc_2 = Arc(t, self.final_place)
                self.arcs.add(arc_1)
                self.arcs.add(arc_2)
                self.transitions.add(t)

            for trans, net in sub_nets:
                self.replace_transition(trans, net)

        elif miner.cut_type == CutType.PARALLEL:
            # print(f"Applying parallel conversion")
            start_transition = Transition("τ")
            end_transition = Transition("τ")
            self.transitions.add(start_transition)
            self.transitions.add(end_transition)
            self.arcs.add(Arc(self.initial_place, start_transition))
            self.arcs.add(Arc(end_transition, self.final_place))
            for t, _ in sub_nets:
                place_0 = self.add_new_place()
                place_1 = self.add_new_place()
                arcs = [
                    Arc(start_transition, place_0),
                    Arc(place_0, t),
                    Arc(t, place_1),
                    Arc(place_1, end_transition)]
                [self.arcs.add(arc) for arc in arcs]
                self.transitions.add(t)

            for trans, net in sub_nets:
                self.replace_transition(trans, net)

        elif miner.cut_type == CutType.INTERLEAVING:
            # print(f"Applying parallel conversion")
            start_transition = Transition("τ")
            end_transition = Transition("τ")
            self.transitions.add(start_transition)
            self.transitions.add(end_transition)
            self.arcs.add(Arc(self.initial_place, start_transition))
            self.arcs.add(Arc(end_transition, self.final_place))
            interleaving_place = self.add_new_place()
            interleaving_place.active = True
            for t, _ in sub_nets:
                place_0 = self.add_new_place()
                place_1 = self.add_new_place()
                arcs = [
                    Arc(start_transition, place_0),
                    Arc(place_0, t),
                    Arc(t, place_1),
                    Arc(place_1, end_transition),
                    Arc(interleaving_place, t),  # Interleaving
                    Arc(t, interleaving_place)]
                [self.arcs.add(arc) for arc in arcs]
                self.transitions.add(t)

            for trans, net in sub_nets:
                self.replace_transition(trans, net)

        elif miner.cut_type == CutType.LOOP:  # Start place should not have incoming edges
            # print(f"Applying loop conversion")
            t_1 = sub_nets[0][0]
            t_2 = sub_nets[1][0]
            st_1 = Transition("τ")
            st_2 = Transition("τ")
            p_1 = self.add_new_place()
            p_2 = self.add_new_place()
            arcs = [
                Arc(self.initial_place, st_1),
                Arc(st_1, p_1),
                Arc(p_1, t_1),
                Arc(t_1, p_2),
                Arc(p_2, st_2),
                Arc(st_2, self.final_place),
                Arc(p_2, t_2),
                Arc(t_2, p_1)]
            [self.arcs.add(arc) for arc in arcs]
            self.transitions.add(t_1)
            self.transitions.add(t_2)
            self.transitions.add(st_1)
            self.transitions.add(st_2)

            for trans, net in sub_nets:
                self.replace_transition(trans, net)

        # p0 -> tau -> p1 improvement (one p0, one p1)
        try:
            transitions_to_remove = []
            arcs_to_remove = set()
            places_to_remove = []
            for transition in self.transitions:
                if "τ" in transition.label:
                    ingoing_places = [a.source for a in self.arcs if a.target == transition]
                    outgoing_places = [a.target for a in self.arcs if a.source == transition]
                    if len(ingoing_places) == len(outgoing_places) == 1 and ingoing_places[0] and \
                            ingoing_places[0] != self.initial_place and outgoing_places[0] != self.final_place:
                        if len([a for a in self.arcs if ingoing_places[0] == a.source]) == 1:  # remove p0
                            transitions_to_remove += [transition]
                            places_to_remove += [ingoing_places[0]]
                            arcs_to_remove |= set([a for a in self.arcs if transition in [a.source, a.target]])
                            for a in [a for a in self.arcs if a.target == ingoing_places[0]]:
                                a.target = outgoing_places[0]
                            for a in [a for a in self.arcs if a.source == ingoing_places[0]]:
                                a.source = outgoing_places[0]
                        elif len([a for a in self.arcs if outgoing_places[0] == a.target]) == 1:  # remove p1
                            transitions_to_remove += [transition]
                            places_to_remove += [outgoing_places[0]]
                            arcs_to_remove |= set([a for a in self.arcs if transition in [a.source, a.target]])
                            for a in [a for a in self.arcs if a.source == outgoing_places[0]]:
                                a.source = ingoing_places[0]
                            for a in [a for a in self.arcs if a.target == outgoing_places[0]]:
                                a.target = ingoing_places[0]
            self.arcs = self.arcs - arcs_to_remove
            [self.transitions.remove(t) for t in transitions_to_remove]
            [self.places.remove(p) for p in places_to_remove]
        except Exception as e:
            print(e)

        # Rename places
        for i in range(2, len(self.places)):
            self.places[i].name = f"P{i}"

        # p0 -1> tau -2> p1 -3> tau -4> p2  =>  p0 -1> tau -4> p2
        try:
            transitions_to_remove = []
            arcs_to_remove = set()
            places_to_remove = []
            new_arcs = set()
            for place in self.places[2:]:
                incoming_transitions = [a.source for a in self.arcs if a.target == place]
                outgoing_transitions = [a.target for a in self.arcs if a.source == place]
                original_places = [a.source for a in self.arcs if a.target in incoming_transitions]
                final_places = [a.target for a in self.arcs if a.source in outgoing_transitions]
                if all([t.label == "τ" for t in incoming_transitions + outgoing_transitions]) and \
                        len(incoming_transitions) == len(outgoing_transitions) == 1 and \
                        len(original_places) == len(final_places) == 1:
                    for a in self.arcs:
                        if a.source in incoming_transitions:
                            for final_place in final_places:
                                new_arcs |= {Arc(a.source, final_place)}
                        if place in [a.source, a.target]:
                            arcs_to_remove |= {a}
                    places_to_remove += [place]

            self.arcs = (self.arcs | new_arcs) - arcs_to_remove
            [self.transitions.remove(t) for t in transitions_to_remove]
            [self.places.remove(p) for p in places_to_remove]
        except Exception as e:
            print(e)

        # Rename places
        for i in range(2, len(self.places)):
            self.places[i].name = f"P{i}"


if __name__ == "__main__":
    from app.miner import get_traces_from_log, get_digraph_from_custom_petri_net
    import os
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
    os.chdir(parent_dir)

    traces = get_traces_from_log("Coopis 2010")
    traces = [list(trace.values())[0] for trace in traces]
    miner = InductiveMinerLifeCycle(traces)
    miner.find_sublogs_cuts()
    print(miner.process_tree)
    petri_net = PetriNetIMLC(miner)
    print(petri_net)
    digraph = get_digraph_from_custom_petri_net(petri_net)
    print(digraph)
