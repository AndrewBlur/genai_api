from datetime import datetime
from ddgs import DDGS

def get_time(format:str):
    """
    Returns the time in specified format

    Parameters
    format : str
             A format string to specify return datetime format

    Returns
    str
        A datetime string
    
    """
    return datetime.now().strftime(format)

def search(query:str,max_results:int=5,source:str="text"):

    """
    Returns search results of the specified query

    Parameters
    query : str
            search query for the search engine

    source : str
             specify the source of results , news or normal ; default to "text"
    
    Returns
    List[dict[str,str]] :
                 A list of search results 
    """

    if source=="text":
       reponse = DDGS().text(query,max_results=max_results)
       return reponse
    elif source == "news":
        return DDGS().news(query,max_results=max_results)
    



tool_schema = [{"type":"function",
               "function":{
                   "name":"get_time",
                   "description":"Get Current Date Time of the computer in specified format",
                   "parameters":{
                       "type":"object",
                       "properties":{
                           "format":{"type":"string", "description":"give the specified format to return with proper percentage format"}
                       },
                       "required":["format"]
                   }
               }},
               {"type":"function",
               "function":{
                   "name":"search",
                   "description":"get the search results from internet using a search query",
                   "parameters":{
                       "type":"object",
                       "properties":{
                           "query":{"type":"string", "description":"query to ask the search engine"},
                           "max_results":{"type":"integer","description":"the maximum results to get from the search engine ; defaults to 5"},
                           "source":{"type":"string","description":"to specify the source of the search results , there are two sources (text) normal search results, (news) search results from news blogs and articles ; defaults to 'text'"}
                       },
                       "required":["query"]
                   }
               }}
               
               ]