from simulator.node import Node
import json

# Each DV node must compute:
# - Its own DV using 1 & 2.  This will be optimal, given the info I have.
# - Whenever either 1 or 2 changes, I must recompute my DV.
# - Whenever my DV changes, send my updated DV to all neighbors.

## NEED TO FIGURE OUT

# deleting nodes, and when links get longer

# We need of the form {(src,dst):(seq,latency)}?


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
        self.dv = {"dv": {id: [0, []]},
                   "timestamp": self.get_time()}
        #       = {"dv": {4: [2, [4]],
        #          2: [2, [2]],
        #          1: [2, [1]]},
        #          "timestamp": INT}

    # Return a string
    def __str__(self):
        return f"Node {self.id}: outbound_links={self.outbound_links} \n dv={self.dv} \n neighbors_dv={self.neighbors_dv} \n"

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

            # For initialization: add neighbor to DV
            if neighbor not in self.dv["dv"].keys():
                self.dv["dv"][neighbor] = [float('inf'), []]



            # For initialization: add neighbor's DV to neighbors_dv
            if neighbor not in self.neighbors_dv.keys():
                self.neighbors_dv[neighbor] = {"dv": {neighbor: [0,[]]},
                                               "timestamp": self.get_time()}

        # Recalcluate DV
        dv_changed = self._recalculate_dv(self.outbound_links.keys())


        # If node's recalculated DV is changed, send to all neighbors
        if dv_changed: 
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


        # Cast each
        dv["dv"] =  {int(k): v for k, v in dv["dv"].items()}

        # store DV in its correct slot
        # Store DV if neighbors_dv does not have the dv (haven't seen this node before) or if the this is the latest dv sent from this neighbor
        if sender_id not in self.neighbors_dv.keys() or dv["timestamp"] >= self.neighbors_dv[sender_id]["timestamp"]:
            self.neighbors_dv[sender_id] = dv

            # For every reachable node of the sender, add it to your dv
            for dest in dv["dv"].keys():
                if dest not in self.dv["dv"].keys():
                    self.dv["dv"][dest] = [float('inf'), []]


        # A link will have been decreased so we want to check if its faster to go through that node
        # Recalculate DV
        dv_changed = self._recalculate_dv(self.outbound_links.keys())

        # Send DV to neighbors
        if dv_changed:
            self._send_dv_to_neighbors()

    def get_next_hop(self, destination):
        """
        Returns the next hop to reach the given destination based on the node's
        current knowledge. If no path to the destination is found, -1 is returned.
        """
        if destination not in list(self.dv["dv"].keys()) or self.dv["dv"][destination][0] == float('inf'):
            return -1

        dest_path = self.dv["dv"][destination][1]

        return dest_path[0]
    
    def _recalculate_dv(self, nodes_to_check):

        # Save node's current DV (dictionary)
        old_dv = {key: value[:] for key, value in self.dv["dv"].items()}

        # Recalculate distance for every node in self.dv
        for dest_node in self.dv["dv"].keys():

            # Cast to be careful
            dest_node = int(dest_node)

            # Don't want to calculate distance to ourself
            if dest_node == self.id:
                continue

            # Start with minimum latency as infinity
            min_latency = float('inf')
            assoc_path = []


            # for neighbor, cost in self.outbound_links.items():
            for neighbor in nodes_to_check:

                # Calculate the latency to neighbor you are checking
                cost = self.outbound_links[neighbor] if neighbor in self.outbound_links.keys() else float('inf')

                # If you don't know neighbor's DV or neighbor cannot reach desired destination node, continue
                if neighbor not in self.neighbors_dv.keys() or dest_node not in self.neighbors_dv[neighbor]["dv"].keys():
                    continue
                
                # Calculate complete path latency
                path_latency = cost + self.neighbors_dv[neighbor]["dv"][dest_node][0]

                # If is infinity, it is meaningless, cannot reach destination
                if path_latency == float('inf'):
                    continue

                # If you are not in the path to get to the destination node
                if self.id not in self.neighbors_dv[neighbor]["dv"][dest_node][1]:

                    # See if path you are on now is less than you're previous minimum latency
                    min_latency = min(min_latency, path_latency)

                    # If current path is now the smallest, update the path list
                    if min_latency == path_latency:
                        assoc_path = [neighbor] + self.neighbors_dv[neighbor]["dv"][dest_node][1]
            
            # Set you self.dv to the shortest path
            self.dv["dv"][dest_node] = [min_latency, assoc_path]

        return old_dv != self.dv["dv"] 


    # Send DV to all neighbors
    def _send_dv_to_neighbors(self):
        self.dv["timestamp"] = self.get_time()
        dv = json.dumps({"sender_id": self.id,
                         "dv": self.dv})
        self.send_to_neighbors(dv)
