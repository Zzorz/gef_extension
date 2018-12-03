from os import system
from pydot import *

class FastGraph(GenericCommand):
    """ Fancy Fastbin """

    _cmdline_ = "graph-fast"
    _syntax_  = "{:s} INDEX".format(_cmdline_)
    _example_ = "{:s} 0".format(_cmdline_)

    def __init__(self):
        super(FastGraph, self).__init__(complete=gdb.COMPLETE_LOCATION)
        return

    def chunk_to_node(self,chunk):
        length = str(2*self.capsize)
        lab = ("Chunk@0x%0"+length+"x\n0x%0"+length+"x | 0x%0"+length+"x\n0x%0"+length+"x | 0x%0"+length+"x")%(chunk.address,chunk.get_prev_chunk_size(),chunk.size,chunk.fd,chunk.bk)
        return Node(hex(chunk.address),label=lab)

    @only_if_gdb_running
    def do_invoke(self, argv):
        def fastbin_index(sz):
            return (sz >> 4) - 2 if SIZE_SZ == 8 else (sz >> 3) - 2

        self.capsize = current_arch.ptrsize
        SIZE_SZ = current_arch.ptrsize
        MAX_FAST_SIZE = (80 * SIZE_SZ // 4)
        NFASTBINS = fastbin_index(MAX_FAST_SIZE) - 1
        graph = Dot(graph_type = 'digraph')
        edges = set()
        chunks = set()
        arena = get_main_arena()

        if not argv:
            err("Missing Index")
            return
        elif int(argv[0]) > NFASTBINS:
            err("Out of range")
            return
        else:
            idx = int(argv[0])


        if arena is None:
            err("Invalid Glibc arena")
            return

        graph.add_node(Node("Fastbin%d"%idx,label='Fastbin|idx=%d,size=0x%x'%(idx,(idx+1)*SIZE_SZ*2)))
        chunk = arena.fastbin(idx)
        if chunk == None or not lookup_address(chunk.address).valid:
            err("empty")
            return
        graph.add_node(self.chunk_to_node(chunk))
        edges.add(tuple((hex(chunk.address),"Fastbin%d"%idx)))

        prev_chunk = None
        while True:
            prev_chunk = chunk
            chunk = GlibcChunk(read_int_from_memory(chunk.address),from_base=True)
            if lookup_address(chunk.address).valid:
                graph.add_node(self.chunk_to_node(chunk))
                edges.add(tuple((hex(chunk.address),hex(prev_chunk.address))))
                if chunk.address in chunks:
                    break
                else:
                    chunks.add(chunk.address)
            else:
                break

        for edge in edges:
            graph.add_edge(Edge(edge[0],edge[1]))
        graph.write_dot('/tmp/graph.dot')
        system('graph-easy /tmp/graph.dot')
        system('rm /tmp/graph.dot')
        return

register_external_command(FastGraph())
