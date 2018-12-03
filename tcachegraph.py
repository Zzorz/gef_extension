from os import system
from pydot import *

class TcacheGraph(GenericCommand):
    """Show tcache graph"""
    _cmdline_ = "graph-tcache"
    _syntax_  = "{:s} INDEX".format(_cmdline_)
    _example_ = "{:s} 0".format(_cmdline_)
    capsize = 0
    tcache = 0
    tcache_enable = 0
    tcache_bins = 0
    tcache_count = 0

    def init(self):
        self.capsize = current_arch.ptrsize
        self.sbrk_base = int(gdb.execute("p mp_.sbrk_base",to_string=True).split()[2].strip(),16)
        self.tcache_bins = int(gdb.execute("p mp_.tcache_bins",to_string=True).split()[2].strip(),16)
        self.tcache_count = int(gdb.execute("p mp_.tcache_count",to_string=True).split()[2].strip(),16)

    def chunk_to_node(self,chunk):
        length = str(2*self.capsize)
        lab = ("Chunk@0x%0"+length+"x\n0x%0"+length+"x | 0x%0"+length+"x\n0x%0"+length+"x | 0x%0"+length+"x")%(chunk.address,chunk.get_prev_chunk_size(),chunk.size,chunk.fd,chunk.bk)
        return Node(hex(chunk.address),label=lab)

    def do_invoke(self, argv):
        self.init()
        if not argv:
            err("Missing Index")
            self.usage()
            return
        elif int(argv[0]) > self.tcache_bins:
            err("Out of range")
            return
        else:
            idx = int(argv[0])

        counts_base = self.sbrk_base + 0x10
        tcache_entry_base = counts_base + self.tcache_bins
        graph = Dot(graph_type = 'digraph')
        counts = int(gdb.execute("x/xb " + str(counts_base + idx),to_string=True).split()[1].strip(),16)
        tcache_entry = read_int_from_memory(tcache_entry_base+self.capsize*idx)
        edges = set()
        chunks = set()

        if lookup_address(tcache_entry).valid:
            graph.add_node(Node('entry%d'%idx,label='idx=%d,size=0x%x,count=%d'%(idx,0x10+idx*0x10,counts)))
        else:
            err("empty entry")
            return

        chunk = GlibcChunk(tcache_entry)
        graph.add_node(self.chunk_to_node(chunk))
        edges.add(tuple((hex(chunk.address),'entry%d'%idx)))
        while True:
            prev_chunk = chunk
            chunk = GlibcChunk(read_int_from_memory(chunk.address))
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

register_external_command(TcacheGraph())
