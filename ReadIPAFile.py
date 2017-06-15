#this script is used to help you to get real time and samples value from IPA file eaiser. 
#Before use this script, you need open a unit command line dialog, and then run this script with command:"python perfun.py"
#this script will run all the tests which "devtest.txt" file lists. Defaultlly, each test will run 3 times. 
#After each run, an IPA file will be generated in current_unit_dir\dt\runs\run1\logs\athena\, this script will parse it and 
#get the samples and real time value. And then, both number will be saved in a log file("perfun.log")
import os

def ParseTestName(rawText):
    #industrialDesign.rep:FfmTest_AOs_Section1WithXformEditing.seq:FfmTest_AOs_Section1WithXformEditing.cxx    
    #->FfmTest_AOs_Section1WithXformEditing
    firstColonPos= rawText.find(":")
    seqPos=rawText.find(".seq")
    return rawText[firstColonPos+1:seqPos]
    
def GetRealTimeAndSamplesFromIPA(IPAFileName):
    #Example, for the following data from IPA
    #Total Time :-  cpu   22.120, real   19.901, monitored thread CPU   10.904
    #Total Samples 17641, sample interval 1ms, Failed Samples 0
    #we have real time= 19.901 and samples=17641
    fHandle=open(IPAFileName)
    realTime,samples=0,0
    realToken="real"
    samplesToken="Total Samples"
    for line in fHandle:
        if line.find("Total Time")>-1:
            realTime=float(line[line.find(realToken)+len(realToken):line.rfind(",")])
            continue
        iTotalSamples=line.find(samplesToken)
        if iTotalSamples > -1 :
            samples=int(line[iTotalSamples+len(samplesToken):line.find(",")])
            break
    fHandle.close()
    return realTime,samples
    
nRunTimesOfEachTest=3    
workDir=os.getcwd()
#get all tests name
testFileName=workDir+"\devtest.txt"
logFileName=workDir+"\perfrun.log"
fLogFile=open(logFileName,"w")
fHandle=open(testFileName)
allLines=fHandle.readlines()
allTestsCmd=[]
allTestsName=[]
for curCmd in allLines:
    if len(curCmd.strip()) < 1:
        continue
    curName=ParseTestName(curCmd)
    allTestsName.append(curName)
    allTestsCmd.append(curCmd)
    print(curCmd)
    print(curName)
fHandle.close()    
nTests=len(allTestsCmd)
print("{0} tests are found:".format(nTests))

#set enviroment vairables for IPA files
os.system("set PRF_MON_IPA_RESULTS=JournalPerformanceMonitor")
os.system("set UGII_CHECKING_LEVEL=0")
os.system("set UGII_CHECKING_PERFORMANCE=1")
for iTest in range(0,nTests):
    curTestName=allTestsName[iTest]
    curCmd= allTestsCmd[iTest]
    #ipaFilePath should be like this: D:\workdir\htxb8s_6_2\dt\runs\run1\logs\athena\0_AT_FfmTest_FFM11011_DAO_Create_A01_t104_001\performance\FfmTest_FFM11011_DAO_Create_A01.results.ipa
    ipaFilePath=workDir+"\\dt\\runs\\run1\\logs\\athena\\"+"0_AT_"+curTestName+"_t104_001"+"\\performance\\"+curTestName+".results.ipa"
    for iTimes in range(0,nRunTimesOfEachTest):
        #begin run test
        os.system("devtest runtest {0}".format(curCmd))
        #IPA file should be created now. Ready to parse it now.
        print("Ready to parse ipa file:{0}\n".format(ipaFilePath))
        realTime,samples= GetRealTimeAndSamplesFromIPA(ipaFilePath)
        msg="{0}rd/nd/th run for test {1}, realTime={2},samples={3}\n".format(iTimes+1,curTestName,realTime, samples)
        print(msg)
        fLogFile.write(msg)
    fLogFile.write("------------------------------------------------------------------------\n")
fLogFile.close()    
print("all tests finish, see {0} for more details".format(logFileName))
