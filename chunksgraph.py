from os import system
from pydot import *

class HeapGraph(GenericCommand):
    """ Fancy heap """

    _cmdline_ = "graph-chunks"
    _syntax_  = "{0} [LOCATION]".format(_cmdline_)

    def __init__(self):
        super(HeapGraph, self).__init__(complete=gdb.COMPLETE_LOCATION)
        self.add_setting("peek_nb_byte", 16, "Hexdump N first byte(s) inside the chunk data (0 to disable)")
        graph = Dot(graph_type = "digraph")
        return

    @only_if_gdb_running
    def do_invoke(self, argv):
        graph = Dot(graph_type = "digraph")
        if not argv:
            heap_section = [x for x in get_process_maps() if x.path == "[heap]"]
            if not heap_section:
                err("No heap section")
                return

            heap_section = heap_section[0].page_start
        else:
            heap_section = int(argv[0], 0)


        arena = get_main_arena()
        if arena is None:
            err("No valid arena")
            return

        nb = self.get_setting("peek_nb_byte")
        current_chunk = GlibcChunk(heap_section, from_base=True)
        counts = 0

        while True:

            if current_chunk.chunk_base_address == arena.top:
                graph.add_node(Node(hex(current_chunk.address),label="top_chunk@"+hex(current_chunk.address)))
                break

            if current_chunk.chunk_base_address > arena.top:
                break

            if current_chunk.size == 0:
                # EOF
                break

            if nb:
                graph.add_node(Node(hex(current_chunk.address),label="Chunk%d@0x%016x\n0x%016x | 0x%016x\n0x%016x | 0x%016x"%(counts,current_chunk.address-0x10,current_chunk.get_prev_chunk_size(),read_int_from_memory(current_chunk.size_addr),current_chunk.fd,current_chunk.bk)))
                counts+=1

            next_chunk = current_chunk.get_next_chunk()
            if next_chunk is None:
                break

            next_chunk_addr = Address(next_chunk.address)
            if not next_chunk_addr.valid:
                # corrupted
                break

            current_chunk = next_chunk
        # print(titlify("Fancy Graph For Chunks!"))
        graph.write_dot('/tmp/graph.dot')
        system("graph-easy /tmp/graph.dot --debug=0")
        system("rm /tmp/graph.dot")
        return

register_external_command(HeapGraph())
