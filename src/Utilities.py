from subprocess import Popen, PIPE
from mutagen.easyid3 import EasyID3
from urlparse import parse_qs, urlparse

import sys, os, errno, re, subprocess

def executeShellCommand(cmd):
    p = Popen(cmd , shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    return out.rstrip(), err.rstrip(), p.returncode

def printDownloadingProgress(progress, file_size):
    percent = progress * 100. / file_size
    status = r"%10d  [%3.2f%%]" % (progress, percent)
    status = status + chr(8) * (len(status) + 1)
    print status

def getFileSizeFromLs(filename):
    res = executeShellCommand("ls -l " + filename)
    out = str(res[0])
    idxf = getNthIndex(out, ' ', 3) + 1
    idxl = getNthIndex(out, ' ', 4)
    return out[idxf:idxl]

def getNthIndex(data, word, nth):
    """
    data:   where to search
    word:   what we search
    nth:    number of the word occurence
    """
    parts= data.split(word, nth + 1)
    if len(parts) <= nth + 1:
        return -1
    return len(data) - len(parts[-1]) - len(word)

def getYoutubeVideoId(url):
    query = urlparse(url)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            p = parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    return None

def getPercentageFromBytes(size, fsize):
    """
        size:  current file size
        fsize: final file size
    """
    return float(size) / float(fsize) * 100

def estimateFFmpegMp4toMp3NewFileSizeInBytes(duration, kbps):
    """
        Very close but not exact.
        
        duration: current file duration in seconds
        kbps: quality in kbps, ex: 320000
        
        Ex:
            estim.:    12,200,000
            real:      12,215,118
    """
    return ((kbps * duration) / 8)

def getFFmpegFileDurationInSeconds(filename):
    cmd = "ffmpeg -i "+ filename +" 2>&1 | grep 'Duration' | cut -d ' ' -f 4 | sed s/,//"
    time = executeShellCommand(cmd)[0]
    h = int(time[0:2])
    m = int(time[3:5])
    s = int(time[6:8])
    ms = int(time[9:11])
    ts = (h * 60 * 60) + (m * 60) + s + (ms/60)
    return ts

def extractFFmpegFileSize(data):
    """
        Attention to carriage returns '/r' or in nano editor '^M'
        Function only extract 1 per line 'm[0] in matches'
    """
    regex = re.compile(r'^size=([^kB\n]+)', re.MULTILINE)
    matches = [m.groups() for m in regex.finditer(data)]
    if matches is not None:
        res = []
        for m in matches:
            text =  str(m[0])
            text = re.sub(r'^[^0-9]*', '', text)
            res.append(text)
        return res

def convertMp4ToMp3(mp4f, mp3f, odir, kbps, efsize=None, 
                    beat=None, on_progress=None, on_finish=None):
    """
        mp4f:           mp4 file, ex: Video.mp4
        mp3f:           mp3 file, ex: Beat.mp3
        odir:           output directory
        kbps:           quality in kbps, ex: 320000
        efsize:         estimated file size
        beat:           beat object containing mp3 information
        on_progress:    called on progress with (size, efsize) in bytes
        on_finish:      called on finish with: (asbpath, beat)

        @Important
        communicate() blocks until the child process returns, so the rest of the lines 
        in your loop will only get executed after the child process has finished running. 
        Reading from stderr will block too, unless you read character by character like here.
        Simple print to console:
            sys.stdout.write(char)
            sys.stdout.flush()
    """
    cmdf = "ffmpeg -i "+ odir+mp4f +" -f mp3 -ab "+ str(kbps) +" -vn "+ odir+mp3f
    lineAfterCarriage = ''
    
    if fileExists(odir + mp3f):
        raise Exception("Cant convert. The file " + odir+mp3f + " exists.\n"+
            "You must delete the file.")
    
    child = subprocess.Popen(cmdf, shell=True, stderr=subprocess.PIPE)
    
    while True:
        char = child.stderr.read(1)
        if char == '' and child.poll() != None:
            break
        if char != '':
            lineAfterCarriage += char
            if char == '\r':
                if on_progress:
                    size = int(extractFFmpegFileSize(lineAfterCarriage)[0])
                    # kb to bytes
                    size *= 1024
                    if efsize:
                        on_progress(size, efsize)
                lineAfterCarriage = ''
    if on_finish:
        on_finish(odir+mp3f, beat)

def writeMP3Metadata(asbpath, beat):
    """
        beat:   object containing the file information
    """
    mp3f = EasyID3(asbpath)
    mp3f["title"] = unicode(beat.getTitle())
    mp3f["artist"] = unicode(beat.getArtist())
    mp3f["album"] = unicode(beat.getAlbum())
    mp3f.save()

