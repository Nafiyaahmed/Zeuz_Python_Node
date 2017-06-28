# -*- coding: utf-8 -*-
# -*- coding: cp1252 -*-
'''
Created on Jun 21, 2017
@author: Built_In_Automation Solutionz Inc.
'''
import sys
import inspect
from Framework.Utilities import CommonUtil
from Framework.Utilities.CommonUtil import passed_tag_list, failed_tag_list
global generic_driver 
generic_driver = None

def Get_Element(step_data_set,driver):
    '''
    This funciton will return "Failed" if something went wrong, else it will always return a single element
    '''
    try:
        sModuleInfo = inspect.stack()[0][3] + " : " + inspect.getmoduleinfo(__file__).name
        generic_driver = driver
        global generic_driver
        # We need to switch to default content just in case previous action switched to something else
        try:
            generic_driver.switch_to_default_content()
        except:
            # Tested that if you switch to default even when it is default doesn't cause anything.
            # for xml, we need to do some verification
            True
        #here we switch driver if we need to
        _switch(step_data_set)
        index_number = _locate_index_number(step_data_set)
        element_query, query_type = _construct_query (step_data_set)
        CommonUtil.ExecLog(sModuleInfo, "Element query used to locate the element: %s. Query method used: %s "%(element_query,query_type), 1)
        if element_query == False:
            return "failed"
        elif query_type == "xpath" and element_query != False:
            return _get_xpath_or_css_element(element_query,"xpath",index_number)
        elif query_type == "css" and element_query != False:
            return _get_xpath_or_css_element(element_query,"css",index_number)
        else:
            return "failed"
    except Exception:
        return CommonUtil.Exception_Handler(sys.exc_info())

def _construct_query (step_data_set): 
    '''
    first find out if in our dataset user is using css or xpath.  If they are using css or xpath, they cannot use any 
    other feature such as child parameter or multiple element parameter to locate the element
    '''
    try:
        collect_all_attribute = [x[0] for x in step_data_set]
        # find out if ref exists.  If it exists, it will set the value to True else False
        child_ref_exits = any("child parameter" in s for s in step_data_set)
        parent_ref_exits = any("parent parameter" in s for s in step_data_set)
        #get all child, element, and parent only
        child_parameter_list = filter(lambda x: 'child parameter' in x[1], step_data_set) 
        element_parameter_list = filter(lambda x: 'element parameter' in x[1], step_data_set) 
        parent_parameter_list = filter(lambda x: 'parent parameter' in x[1], step_data_set) 
        
        if "css" in collect_all_attribute and "xpath" not in collect_all_attribute:
            # return the raw css command with css as type.  We do this so that even if user enters other data, we will ignore them.  
            # here we expect to get raw css query
            return ((filter(lambda x: 'css' in x[0], step_data_set) [0][2]), "css")
        elif "xpath" in collect_all_attribute and "css" not in collect_all_attribute:
            # return the raw xpath command with xpath as type.  We do this so that even if user enters other data, we will ignore them.  
            # here we expect to get raw xpath query
            return ((filter(lambda x: 'xpath' in x[0], step_data_set) [0][2]), "xpath" )       
        elif child_ref_exits == False and parent_ref_exits == False :
            '''  If  there are no child or parent as reference, then we construct the xpath differently'''
            #first we collect all rows with element parameter only 
            xpath_element_list = (_construct_xpath_list(element_parameter_list))
            return (_construct_xpath_string_from_list(xpath_element_list), "xpath")
        elif child_ref_exits == True and parent_ref_exits == False:
            '''  If  There is child but making sure no parent'''
            xpath_child_list =  _construct_xpath_list(child_parameter_list,True)
            child_xpath_string = _construct_xpath_string_from_list(xpath_child_list) 
            xpath_element_list = _construct_xpath_list(element_parameter_list)
            #Take the first element, remove ]; add the 'and'; add back the ]; put the modified back into list. 
            xpath_element_list[1] = (xpath_element_list[1]).replace("]","") + ' and ' + child_xpath_string + "]"
            return (_construct_xpath_string_from_list(xpath_element_list), "xpath")
        elif child_ref_exits == False and parent_ref_exits == True:
            '''  If  There is parent but making sure no child'''
            xpath_parent_list =  _construct_xpath_list(parent_parameter_list)
            parent_xpath_string = _construct_xpath_string_from_list(xpath_parent_list) 
            xpath_element_list = _construct_xpath_list(element_parameter_list,True)
            #Take the first element, remove ]; add the 'and'; add back the ]; put the modified back into list. 
            xpath_element_list[1] = (xpath_element_list[1]).replace("]","") + ' and ' + parent_xpath_string + "]"
            return (_construct_xpath_string_from_list(xpath_element_list), "xpath")
        else:
            return False, False
    except Exception:
        return CommonUtil.Exception_Handler(sys.exc_info())

def _construct_xpath_list(parameter_list,add_dot=False):
    '''
    This function constructs the raw data from step data into a xpath friendly format but in a list
    '''
    try:
        element_main_body_list = []
        #these are special cases where we cannot treat their attribute as any other attribute such as id, class and so on...  
        excluded_attribute = ["*text", "text", "tag", "css", "index","xpath","switch frame","switch window","switch alert","switch active"]
        for each_data_row in parameter_list:
            attribute = (each_data_row[0].strip()).lower()
            attribute_value = each_data_row[2]
            if attribute == "text":
                text_value = '[text()="%s"]'%attribute_value
                element_main_body_list.append(text_value)
            elif attribute == "*text":
                text_value = '[contains(text(),"%s")]'%attribute_value    
                element_main_body_list.append(text_value)
            elif attribute not in excluded_attribute and '*' not in attribute:
                other_value = '[@%s="%s"]'%(attribute,attribute_value)
                element_main_body_list.append(other_value)
            elif attribute not in excluded_attribute and '*' in attribute:
                other_value = '[contains(@%s,"%s")]'%(attribute.split('*')[1],attribute_value)
                element_main_body_list.append(other_value)
        #we do the tag on its own  
        #tag_was_given = any("tag" in s for s in parameter_list)
        if "tag" in [x[0] for x in parameter_list]:
            tag_item = "//"+ filter(lambda x: 'tag' in x, parameter_list)[0][2]
        else:
            tag_item = "//*"
        if add_dot != False:
            tag_item = '.'+tag_item
        element_main_body_list.append(tag_item)
        #We need to reverse the list so that tag comes at the begining 
        return list(reversed(element_main_body_list))
    except Exception:
        return CommonUtil.Exception_Handler(sys.exc_info())

def _construct_xpath_string_from_list(xpath_list): 
    '''
    in this function, we simply take the list and construct the actual query in string
    '''
    try:
        xpath_string_format = ""
        for each in xpath_list:
            xpath_string_format = xpath_string_format+each   
        return  xpath_string_format
    except Exception:
        return CommonUtil.Exception_Handler(sys.exc_info())    

def _switch(step_data_set):
    "here we switch the global driver to any of the switch call"
    try:
        sModuleInfo = inspect.stack()[0][3] + " : " + inspect.getmoduleinfo(__file__).name
        # find if frame switch is there.  If user enters more than one frame, it will ignore
        # user should enter multiple frame in this order parent > child > grand child ... and so on
        if "switch frame" in [x[0] for x in step_data_set]: 
            frame_switch = filter(lambda x: 'switch frame' == x[0], step_data_set) [0][2]
            # first we split by > and then we reconstruct the list by striping trailing spaces and lowering all letters
            frame_switch_list = [(x.strip()).lower() for x in (frame_switch.split(">"))]
            # we switch each frame in order 
            for each_frame in frame_switch_list:
                CommonUtil.ExecLog(sModuleInfo, "switching frame; %s"%each_frame, 1)
                generic_driver.switch_to_frame(each_frame)
            return  True 
        elif "switch window" in [x[0] for x in step_data_set]: 
            #get the value of switch window
            window_switch = filter(lambda x: 'switch window' == x[0], step_data_set) [0][2]
            # first we split by > and then we reconstruct the list by striping trailing spaces and lowering all letters
            window_switch_list = [(x.strip()).lower() for x in (window_switch.split(">"))]
            # we switch each window in order 
            for each_window in window_switch_list:
                CommonUtil.ExecLog(sModuleInfo, "switching window; %s"%each_window, 1)
                generic_driver.switch_to_window(each_window) 
            return  True  
        elif "switch alert" in [x[0] for x in step_data_set]:  
            generic_driver.switch_to_alert()
            CommonUtil.ExecLog(sModuleInfo, "switching to alert", 1)
            return  True 
        elif "switch active" in [x[0] for x in step_data_set]:  
            CommonUtil.ExecLog(sModuleInfo, "switching to active element", 1)
            generic_driver.switch_to_active_element()
            return  True 
        else:
            return True
    except Exception:
        return CommonUtil.Exception_Handler(sys.exc_info())   

def _get_xpath_or_css_element(element_query,css_xpath, index_number=False):  
    '''
    Here, we actually execute the query based on css/xpath and then analyze if there are multiple.
    If we find multiple we give warning and send the first one we found.
    We also consider if user sent index.  If they did, we send them the index they provided
    '''
    try: 
        all_matching_elements = []
        sModuleInfo = inspect.stack()[0][3] + " : " + inspect.getmoduleinfo(__file__).name
        if css_xpath == "xpath":
            all_matching_elements = generic_driver.find_elements_by_xpath(element_query)
        elif css_xpath == "css":
            all_matching_elements = generic_driver.find_elements_by_css_selector(element_query)
            
        if len(all_matching_elements)== 0:
            return False
        elif len(all_matching_elements)==1 and index_number == False:
            return all_matching_elements[0]
        elif len(all_matching_elements)>1 and index_number == False:
            CommonUtil.ExecLog(sModuleInfo, "Warning: found %s elements with given condition.  Returning first item.  Consider providing index"%len(all_matching_elements), 2)
            return all_matching_elements[0]  
        elif len(all_matching_elements)==1 and abs(index_number) >0:
            CommonUtil.ExecLog(sModuleInfo, "Warning: we only found single element but you provided an index number greater than 0.  Returning the only element", 2)
            return all_matching_elements[0]
        elif len(all_matching_elements) >1 and index_number != False:
            if (len(all_matching_elements)-1) < abs(index_number):
                CommonUtil.ExecLog(sModuleInfo,  "Warning: your index: %s exceed the the number of elements found: %s. Returning the last element instead.  Index used:%s"%(index_number, len(all_matching_elements)-1), 2)
                return all_matching_elements[(len(all_matching_elements)-1)]
            else:
                CommonUtil.ExecLog(sModuleInfo, "Total elements found are: %s but returning element number: %s" %(len(all_matching_elements),index_number), 2)
                return all_matching_elements[index_number]    
        else:
            return "failed"   
    except Exception:
        return CommonUtil.Exception_Handler(sys.exc_info())     

def _locate_index_number(step_data_set):
    '''
    Check if index exists, if it does, get the index value.
    if we cannot convert index to integer, set it to False
    '''
    try:
        if "index" in [x[0] for x in step_data_set]:
            index_number = filter(lambda x: 'index' in x[0], step_data_set) [0][2] 
            try:
                index_number = int (index_number)
            except:
                index_number =False
        else:
            index_number =False
        return index_number
    except Exception:
        return CommonUtil.Exception_Handler(sys.exc_info())
    


