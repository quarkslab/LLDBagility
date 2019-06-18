#include <stdlib.h>
#include <pthread.h>
#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <pthread.h>
#include <unistd.h>

#include "FDP.h"
#include "FDP_structs.h"



//TODO ! Unit Tests

volatile uint32_t count_per_sec = 0;
volatile bool bIsRunning = true;

bool FDP_DummyReadRegister(void* pUserHandle, uint32_t u32CpuId, FDP_Register u8RegisterId, uint64_t* pRegisterValue)
{
    *pRegisterValue = count_per_sec;
    count_per_sec = 0;
    return true;
}


bool FDP_DummyWriteRegister(void* pUserHandle, uint32_t u32CpuId, FDP_Register u8RegisterId, uint64_t pRegisterValue)
{
    //uint16_t t = rand();
    //for(int i = 0; i<t; i++){};
    count_per_sec++;
    return true;
}

bool FDP_DummyGetCpuCount(void* pUserHandle, uint32_t* pCpuCount)
{
    *pCpuCount = 0x42;
    return true;
}



void* FDP_UnitTestClient(void* lpParameter)
{
    FDP_SHM* pFDPClient = (FDP_SHM*)lpParameter;
    //Waiting for FDPServer star
    while (pFDPClient->pFdpServer->bIsRunning == false)
    {
        printf(".");
    }

    while(bIsRunning){
        FDP_WriteRegister(pFDPClient, 0, FDP_CS_REGISTER, 0xCAFECAFECAFECAFE);
    }
    return NULL;
}


void* counter_core(void* lpParameter)
{
    FDP_SHM* pFDPClient = (FDP_SHM*)lpParameter;
    uint64_t count = 0;
    for(int i=0; i<10; i++){
    	printf("...\n");
        sleep(1);
	printf("Read...\n");
        FDP_ReadRegister(pFDPClient, 0, FDP_CS_REGISTER, &count);
        printf("%llu/sec\n", count);
    }
    bIsRunning = false;
    exit(0);
    return NULL;
}

bool FDP_ClientServerTest()
{
    //Building FDP Server Interface
    FDP_SERVER_INTERFACE_T FDPServerInterface;
    //FDPServerInterface.bIsRunning = true;
    FDPServerInterface.pUserHandle = NULL;
    FDPServerInterface.pfnReadRegister = FDP_DummyReadRegister;
    FDPServerInterface.pfnWriteRegister = FDP_DummyWriteRegister;
    FDPServerInterface.pfnGetCpuCount = FDP_DummyGetCpuCount;
    FDP_SHM* pFDPServer = FDP_CreateSHM("FDP_TEST");

    if (pFDPServer == NULL)
    {
        printf("Failed to FDP_CreateSHM\n");
        return false;
    }
    if (FDP_SetFDPServer(pFDPServer, &FDPServerInterface) == false)
    {
        printf("Failed to FDP_SerFDPServer\n");
        return false;
    }

    /*//Create a fake Client...
    HANDLE hThreadServer = INVALID_HANDLE_VALUE;
    hThreadServer = CreateThread(NULL, 0, FDP_UnitTestClient, pFDPServer, 0, 0);
    if (hThreadServer == INVALID_HANDLE_VALUE)
    {
        printf("Failed to CreateThread\n");
        return false;
    }*/
    pthread_t threadServer = 0;
    for(int i=0; i<1; i++){
        if(pthread_create(&threadServer, NULL, FDP_UnitTestClient, pFDPServer) != 0){
            printf("Failed to phread_create\n");
            return false;
        }
    }

    pthread_t threadCounter = 0;
    if(pthread_create(&threadCounter, NULL, counter_core, pFDPServer) != 0){
        printf("Failed to phread_create\n");
        return -1;
    }


    if (FDP_ServerLoop(pFDPServer) == false)
    {
        printf("Failed to FDP_ServerLoop\n");
        return false;
    }
    Clean:
    //Closing server
    FDPServerInterface.bIsRunning = false;
    //WaitForSingleObject(hThreadServer, INFINITE);
    pthread_join(threadServer, NULL);
    return true;
}


int main(int argc, char* argv[])
{
    FDP_ClientServerTest();
    return 0;
}
