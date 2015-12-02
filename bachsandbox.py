from music21 import *
from sets import *
import operator
import numpy
import scipy.stats
import csv
import matplotlib.pyplot as plt
import pickle
from music21.stream import Stream
import collections

"""
A quick and dirty set of tools for pulling apart the voicings in the Bach chorales.
Relies on the corpus included with music21.
"""

def gapTally():
    '''
    For a given "maximum gap" size, search through all the chorale voicing slices
    Tally how many voicings contain a gap of that size or larger
    Convert that tally into a percentage of the total voicings
    Make a plot of that percentage versus maxgap size
    '''
    allSlices = csv.reader(open('Chorale4VoicingsList.csv', 'rb'))
    listofSlices = []
    #make list of slices
    for slice in allSlices:
        listofSlices.append(slice)
    numSlices = len(listofSlices)
    gapsizes = []
    gappercents = []
    #tally up all gaps larger than n semitones, where n iterates from 7 up to 50
    for gapsize in range(7,50):
        print gapsize
        numGapped = 0.0
        for i, slice in enumerate(listofSlices):
            #if i > 10:
                #break
            #if adjacent voice distance greater than the current gapsize, count it
            if (int(slice[2]) - int(slice[1])) > gapsize or (int(slice[3]) - int(slice[2])) > gapsize:
                numGapped += 1
        #once there are none bigger than gapsize, we've found the biggest
        if numGapped == 0.0:
            print 'max gap size is', gapsize-1
            break
        gappercents.append(numGapped/numSlices)
        gapsizes.append(gapsize)
    '''
    #make a quick pyplot
    plt.plot(gapsizes,gappercents)
    plt.ylabel('Proportion of voicings with gaps of at least size x')
    plt.xlabel('Maximum recommended semitonal gap-size (bass excluded)')
    plt.title('Voicings violating gap-size heuristics')
    plt.show()
    '''
        
def findBigGaps():
    """
    Look through the chorales and find ones where S-A > 19 or A-T > 19.
    Outputs a list of those chorales sorted by how many such voicings are in them
    """
    #sliceTally = {}
    pieceList = collections.Counter()
    keyList = collections.Counter()
    pieceAndKey = collections.Counter()
    ALLkeylist = collections.Counter()
    #from music21, call the corpus of Bach chorales
    allBachChorales = corpus.getBachChorales()
    for pieceName in allBachChorales:
        keyConfDict = {}
        bestKeyDict = {}
        #this is the time-consuming music21 parse command... streams ensue
        theChorale = corpus.parse(pieceName)
        #strip out any weird instrumental hangers-on
        for thePart in theChorale.parts:
            if thePart.getInstrument().bestName() not in ['Soprano', 'S.','Alto','A.','Tenor','T.','Bass','B.']:
                theChorale.remove(thePart)
        theSoloChords = theChorale.chordify().flat.getElementsByClass('Chord')
        #now that the slices are pulled, check each one to see if it's of the right quality
        for i,someChord in enumerate(theSoloChords):
            windStream = stream.Stream()
            #run keyfinding on windows of length 8, but don't look beyond end of stream
            for j in range(8):
                if i + j + 1 == len(theSoloChords):
                    break
                #print someChord
                windStream.append(theSoloChords[i+j])
            if len(windStream) == 0:
                break
            #windowed key analysis; use Aarden-Essen, matches folky harmonies
            theKey = windStream.analyze('Aarden')
            #print theKey
            #print theKey.correlationCoefficient
            '''
            theTonic = str(theKey).split(' ')[0]
            theMode = str(theKey).split(' ')[1]
            theKeyPC = pitch.Pitch(theTonic).pitchClass
            '''
            #see if that particular key window yields best confidence for particular chord
            for j,chd in enumerate(windStream):
                try:
                    if keyConfDict[str(i+j)] < theKey.correlationCoefficient:
                        keyConfDict[str(i+j)] = theKey.correlationCoefficient
                        bestKeyDict[str(i+j)] = (theKey.tonic,theKey.mode)
                except KeyError:
                    keyConfDict[str(i+j)] = theKey.correlationCoefficient
                    bestKeyDict[str(i+j)] = (theKey.tonic,theKey.mode)
            #now every chord is assigned to its most confident 8-length key
        #print sorted(bestKeyDict.iteritems(), key=operator.itemgetter(0),reverse=True)
        #now look for chords with all 4 voices, transpose them to local keys, find gaps
        for i,someChord in enumerate(theSoloChords):
            sorted_someMIDI = sorted([p.midi for p in someChord.pitches])
            if len(sorted_someMIDI) != 4:
                continue
            try:
                localKey = bestKeyDict[str(i)]
            except KeyError:
                #print 'No key!',i,someChord
                break
            if (sorted_someMIDI[2] - sorted_someMIDI[1]) > 12 or (sorted_someMIDI[3] - sorted_someMIDI[2] > 12):
                pieceList[str(pieceName)] +=  1
                keyList[str(localKey)] += 1
                pieceAndKey[str(pieceName)] = str(localKey)
            ALLkeylist[str(localKey)] += 1
    sorted_pieceList = sorted(pieceList.iteritems(), key=operator.itemgetter(1), reverse=True)
    sorted_keyList = sorted(keyList.iteritems(), key=operator.itemgetter(1),reverse=True)
    sorted_ALLkeylist = sorted(ALLkeylist.iteritems(), key=operator.itemgetter(1),reverse=True)
    #print sorted_keyList
    #print pieceAndKey
    print sorted_ALLkeylist
    #export the tally as a csv file
    '''
    csvName = 'chorales gapped voicing keys.csv'
    x = csv.writer(open(csvName, 'wb'))
    for pair in sorted_keyList:
        x.writerow([pair[0], pair[1]])
    '''
    csvName = 'chorale 4-vcgs aelocalKey.csv'
    x = csv.writer(open(csvName, 'wb'))
    for pair in sorted_ALLkeylist:
        x.writerow([pair[0], pair[1]])

def getVoicingCSV():
    #Blindly tally up most common voicings
    myData = pickle.load( open ('ChoraleSlicesDict.pkl', 'rb') )
    voicingList = []
    for i, slice in enumerate(myData):
        if slice['type'] == 'start' or slice['type'] == 'end':
            continue
        sliceVoicing = slice['voicing type']
        #only count voicings with 4 parts
        if len(sliceVoicing) == 4:
            voicingList.append(sliceVoicing)
        #if i > 20:
            #break
    #package up csv
    #write the CSV
    file = open('Chorale4VoicingsList.csv', 'wb')
    lw = csv.writer(file)
    for row in voicingList:
        lw.writerow(row)
        
#getVoicingCSV()
#gapTally()
findBigGaps()