import os
import pickle
import shutil

from mercurial import node

svn_subcommands = { }

def register_subcommand(name):
    def inner(fn):
        svn_subcommands[name] = fn
        return fn
    return inner


def generate_help():
    ret = ['', 'hg svn subcommand\n', 'Subcommands:\n']

    for name, func in sorted(svn_subcommands.items()):
        short_description = (func.__doc__ or '').split('\n')[0]
        ret.append(" %-10s  %s" % (name, short_description))

    return "\n".join(ret) + '\n'


def wipe_all_files(hg_wc_path):
    files = [f for f in os.listdir(hg_wc_path) if f != '.hg']
    for f in files:
        f = os.path.join(hg_wc_path, f)
        if os.path.isdir(f):
            shutil.rmtree(f)
        else:
            os.remove(f)

REVMAP_FILE_VERSION = 1
def parse_revmap(revmap_filename):
    revmap = {}
    f = open(revmap_filename)
    try:
        # Remove compat code after March of 2009. That should be more than long
        # enough.
        revmap = pickle.load(f)
        f.close()
        f = open(revmap_filename, 'w')
        f.write('1\n')
        for key, value in sorted(revmap.items()):
            f.write('%s %s %s\n' % (str(key[0]), node.hex(value), key[1] or ''))
        f.close()
    except:
        f.close()
        f = open(revmap_filename)
        ver = int(f.readline())
        if ver == 1:
            for l in f:
                revnum, node_hash, branch = l.split(' ', 2)
                if branch == '\n':
                    branch = None
                else:
                    branch = branch[:-1]
                revmap[int(revnum), branch] = node.bin(node_hash)
            f.close()
        else:
            print ('Your revmap was made by a newer version of hgsubversion.'
                   ' Please upgrade.')
            raise NotImplementedError
    return revmap


class PrefixMatch(object):
    def __init__(self, prefix):
        self.p = prefix
    
    def files(self):
        return []
    
    def __call__(self, fn):
        return fn.startswith(self.p)

def outgoing_revisions(ui, repo, hg_editor, reverse_map):
    """Given a repo and an hg_editor, determines outgoing revisions for the
    current working copy state.
    """
    outgoing_rev_hashes = []
    working_rev = repo.parents()
    assert len(working_rev) == 1
    working_rev = working_rev[0]
    if working_rev.node() in reverse_map:
        return
    while (not working_rev.node() in reverse_map
           and working_rev.node() != node.nullid):
        outgoing_rev_hashes.append(working_rev.node())
        working_rev = working_rev.parents()
        assert len(working_rev) == 1
        working_rev = working_rev[0]
    if working_rev.node() != node.nullid:
        return outgoing_rev_hashes
