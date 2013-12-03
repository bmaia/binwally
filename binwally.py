#!/usr/bin/python

import ssdeep
import os, sys

blocksize = 1024 * 1024

def reportdiffs(unique1, unique2, dir1, dir2, diffs):
    """
    Generate diffs report for unique files and dirs
    Unique files have a matching score of 0
    """
    if unique1:
        for file in unique1:
            root = os.path.join(dir1,file)
            if os.path.isfile(root):
                print '  <<< unique ',root
                diffs.append(0)
            else:
                for root, dir, files in os.walk(root):
                    for file in files:
                        print '  <<< unique ',os.path.join(root,file)
                        diffs.append(0)                
    if unique2:
        for file in unique2:
            root = os.path.join(dir2,file)
            if os.path.isfile(root):
                print '  >>> unique ',root
                diffs.append(0)
            else:
                for root, dir, files in os.walk(root):
                    for file in files:
                        print '  >>> unique ',os.path.join(root,file)
                        diffs.append(0)

def difference(seq1, seq2):
    """
    Return all items in seq1 only
    """
    return [item for item in seq1 if item not in seq2]

def intersect(seq1, seq2):
    """
    Return all items in both seq1 and seq2
    """
    return [item for item in seq1 if item in seq2]

def comparedirs(dir1, dir2, diffs, files1=None, files2=None):
    """
    Compare directory contents, but not actual files
    """
    files1  = os.listdir(dir1) if files1 is None else files1
    files2  = os.listdir(dir2) if files2 is None else files2
    unique1 = difference(files1, files2)
    unique2 = difference(files2, files1)
    reportdiffs(unique1, unique2, dir1, dir2, diffs)
    return not (unique1 or unique2)               # true if no diffs

def comparetrees(dir1, dir2, diffs):
    """
    Compare all subdirectories and files in two directory trees
    Same files have a matching score of 100
    Symlinks have a matching score of 100
    Different files have a matching score calculated using ssdeep (0 to 100)
    """
    names1 = os.listdir(dir1)
    names2 = os.listdir(dir2)    
    comparedirs(dir1, dir2, diffs, names1, names2)
    common = intersect(names1, names2)
    missed = common[:]

    # compare contents of files in common
    for name in common:
        path1 = os.path.join(dir1, name)
        path2 = os.path.join(dir2, name)
        if os.path.isfile(path1) and os.path.isfile(path2):
            missed.remove(name)
            file1 = open(path1, 'rb')
            file2 = open(path2, 'rb')
            while True:
                bytes1 = file1.read(blocksize)
                bytes2 = file2.read(blocksize)
                if (not bytes1) and (not bytes2):   # same file
                    print '  100 matches','/'.join(path1.split('/')[1:])
                    diffs.append(100)
                    break
                if bytes1 != bytes2:    # different content
                    score = ssdeep.compare(ssdeep.hash_from_file(path1),ssdeep.hash_from_file(path2))
                    print str(score).rjust(5),'differs','/'.join(path1.split('/')[1:])
                    diffs.append(score)
                    break

    # recur to compare directories in common
    for name in common:
        path1 = os.path.join(dir1, name)
        path2 = os.path.join(dir2, name)
        if os.path.isdir(path1) and os.path.isdir(path2):
            missed.remove(name)
            comparetrees(path1, path2, diffs)

    # same name but not both files or dirs (symlinks)
    for name in missed:
        diffs.append(100)
        print('    - ignored '+name+' (symlink)')

def getargs():
    "Command-line arguments"
    try:
        dir1, dir2 = sys.argv[1:]
    except:
        print '\
  \nBinwally: Binary and Directory tree comparison tool\
  \n          using the Fuzzy Hashing concept (ssdeep)\n\
  \nBernardo Rodrigues, http://w00tsec.blogspot.com\n\
  \nUsage: python %s dir1 dir2' % os.path.basename(sys.argv[0])+'\n'
        sys.exit(1)
    else:
        return (dir1, dir2)
                
if __name__ == '__main__':
    dir1, dir2 = getargs()
    diffs = []
    totalscore = 0

    # command line arguments are both dirs
    if os.path.isdir(dir1) & os.path.isdir(dir2):
        print '\nSCORE RESULT  PATH'
        comparetrees(dir1, dir2, diffs)
        if not diffs:
            print('No diffs found\n')
        else:
            for score in diffs:
                totalscore += score
            print '\nTotal files compared:',len(diffs)
            print 'Overall match score: ',str(totalscore/len(diffs))+'%\n'
    else:
        try:
            # command line arguments are both files
            score = ssdeep.compare(ssdeep.hash_from_file(dir1),ssdeep.hash_from_file(dir2))
            print 'Overall match score: ',str(score)+'%\n'

        except:
            print 'Invalid Files/Folders: Aborting...'
            sys.exit(1)

