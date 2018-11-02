# TaigaTool

Simple tool that give some basic information about a Taiga Scrum board.

The tool will plot a simple MatPlot lib graph to show when tasks where moved on a Sprint. 

A config file (config.json) needs to be defined.

The config file is given (comment are not allowed in JSON).

{
    "slug": "slug", 	
    
    "password" : null,		// null for public repos for private set password	
    
    "username" : null,		//  null for public repos for private set username	
    
    "sprintNumber" : 0,		// if null program will ask for sprint number, 0 is newest sprint				
    "plotUS" : true			// true will plot some data for US, false will skip this step		
}


slug is the project name on Taiga (everything after project/ in the URL)

run python TaigaTest.py.
