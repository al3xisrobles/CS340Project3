from simulator.node import Node
import json
import time

# Each DV node must compute:
# - Its own DV using 1 & 2.  This will be optimal, given the info I have.
# - Whenever either 1 or 2 changes, I must recompute my DV.
# - Whenever my DV changes, send my updated DV to all neighbors.

## NEED TO FIGURE OUT

# deleting nodes, and when links get longer


# STEPS:
# link_has_been_updated gets called
# update outbound link instance variable 
# recalculate its own dv
# if it changes, send it to its neighbors

# process_incoming_routing_message gets called
# update its own neighboring distance vectors with dv just received
# recalculate its own dv
# if it changes, send it to its neighbors

class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)

        # Each DV node must store:
        # 1. Its outbound links (who do they connect to, and at what cost?)
        self.outbound_links = {} # neighbor_id -> cost
        #                   = {4: 2,
        #                      2: 2,
        #                      1: 2}

        # 2. Each neighbor’s latest DV (who can I reach through neighbors?)
        self.neighbors_dv = {} # neighbor_id -> {link -> [cost, AS_PATH]}
        #                 = {4: {"dv": {3: [2, [3]],
        #                        1: [4, [1]],
        #                        2: [4, [2]]},
        #                        "timestamp": INT},
        #                    2: {3: [2, []],
        #                        1: [2, []],
        #                        0: [4, [0]]},
        #                    1: {0: [2, []],
        #                        2: [2, []],
        #                        3: [2, []]}}

        # 3. Its own distance vector (DV) to each destination
        self.dv = {"dv": {},
                   "timestamp": self.get_time()}
        #       = {"dv": {4: [2, [4]],
        #          2: [2, [2]],
        #          1: [2, [1]]},
        #          "timestamp": INT}

    # Return a string
    def __str__(self):
        return f"Node {self.id}: outbound_links={self.outbound_links} \n dv={self.dv} \n neighbors_dv={self.neighbors_dv}"

    # When the link costs change, update its DV and notify neighbors
    # called for nodes at both ends of link that is updated
    def link_has_been_updated(self, neighbor, latency):
        """
        # 1. Node detects local link cost change
        # 2. Recalculates distance vector
        # 3. If DV changed, notify neighbors (in JSON format, with timestamp)
        """

        # Variable to track whether we want to send our own dv to our neighbors
        # Applicable when latency to neighbor decreases (we make the change
        # to self.dv in this function), but then nothing changes in recalculate_dv
        send_to_neighbors = False


        # If latency = -1, link is to be deleted
        if latency == -1:

            # Remove neighbor from outgoing_links
            del self.outbound_links[neighbor]

            # Remove neighbor from neighbor_dv
            del self.neighbors_dv[neighbor]

        # Link's cost has been changed
        else:

            # Update cost to neighbor
            self.outbound_links[neighbor] = latency

            # For initialization: add neighbor to DV and neighbors dv
            if neighbor not in list(self.dv["dv"].keys()):
                self.dv["dv"][neighbor] = [latency, [neighbor]]
                self.neighbors_dv[neighbor] = {"dv": {},
                                               "timestamp": self.get_time()}

            # Update my dv's link if needed
            if latency < self.dv["dv"][neighbor][0] or self.dv["dv"][neighbor][1] == [neighbor]:
                self.dv["dv"][neighbor][0] = latency
                self.dv["dv"][neighbor][1] = [neighbor]
                send_to_neighbors = True



        # Recalcluate DV
        dv_changed = self._recalculate_dv(neighbor)

        # If node's recalculated DV is changed, send to all neighbors
        if dv_changed or send_to_neighbors:
            self._send_dv_to_neighbors()

    # You must record the new information within the node, and (depending on
    # the message contents) you may need to send messages to neighbors.
    # send the entire DV, maybe add the dest that changed
    def process_incoming_routing_message(self, m):

        # Message
        message = json.loads(m)

        # Sender ID
        sender_id = int(message["sender_id"])

        # Parse DV from sender
        dv = message["dv"]

        # store DV in its correct slot
        # Store DV if neighbors_dv does not have the dv or if the this is the latest dv sent from this neighbor
        if not self.neighbors_dv[sender_id]["dv"] or dv["timestamp"] > self.neighbors_dv[sender_id]["timestamp"]:
            self.neighbors_dv[sender_id] = dv

        # Recalculate DV
        dv_changed = self._recalculate_dv(sender_id)

        # Send DV to neighbors
        if dv_changed:
            self._send_dv_to_neighbors()

    def get_next_hop(self, destination):
        """
        Returns the next hop to reach the given destination based on the node's
        current knowledge. If no path to the destination is found, -1 is returned.
        """
        if destination not in list(self.dv["dv"].keys()):
            return -1

        dest_path = self.dv["dv"][destination][1]

        return dest_path[0]





        # if destination == self.id:
        #     return self.id
        # next_hop = -1
        # min_cost = float("inf")
        # for neighbor, dv in self.neighbors_dv.items():
        #     if destination in dv and dv[destination] < min_cost:
        #         next_hop = neighbor
        #         min_cost = dv[destination]
        # return next_hop

    # Recompute this node's distance vector and return True if it has changed
    def _recalculate_dv(self, node_to_check):
        """
        Recomputes the node's distance vector based on its outbound links and
        its neighbors' latest distance vectors. Returns True if the node's
        distance vector has changed, False otherwise.
        """

        # Save node's current DV (dictionary)
        old_dv = self.dv["dv"].copy()

        # Cost from current node to node_to_check
        dist_to_checking_node = self.dv["dv"][node_to_check][0]

        # Get updated node_to_check's DV (dictionary) from current 
        # node's neighbors' data
        checking_dv = self.neighbors_dv[node_to_check]["dv"]

        # For each node that the node_to_check connects to
        for dest, (checking_latency, checking_path) in checking_dv.items():
            
            # Don't want to calculate distance to current node
            if dest == self.id:
                continue

            # Ensure that neighbors' DV's vertices are in current node's DV

            # SOMETHING WEIRD HAPPENING HERE I THINK
            if dest not in list(self.dv["dv"].keys()):
                self.dv["dv"][dest] = [float('inf'), []]

            # Calculate the cost from current node to the dest node, through node_to_check
            new_latency_to_dest = dist_to_checking_node + checking_latency

            # If this distance is less than current node to checking node, update my DV
            if new_latency_to_dest < self.dv["dv"][dest][0]:

                # Ensure that we are not in a loop
                if self.id not in checking_path:
                    
                    # Update our DV with new cost and path to destination
                    self.dv["dv"][dest] = [new_latency_to_dest, [node_to_check] + checking_path]

        # Return True if dv has been updated, False otherwise
        return old_dv != self.dv["dv"]

    # Send DV to all neighbors
    def _send_dv_to_neighbors(self):
        self.dv["timestamp"] = self.get_time()
        dv = json.dumps({"sender_id": self.id,
                         "dv": self.dv})
        self.send_to_neighbors(dv)
