"""
Interface to the env_batch.xml file.  This class inherits from EnvBase
"""
from CIME.XML.standard_module_setup import *
from CIME.utils import convert_to_type
from env_base import EnvBase
from CIME.utils import convert_to_string
from copy import deepcopy

logger = logging.getLogger(__name__)

class EnvBatch(EnvBase):

    def __init__(self, case_root=None, infile="env_batch.xml"):
        """
        initialize an object interface to file env_batch.xml in the case directory
        """
        if case_root is None:
            case_root = os.getcwd()
        EnvBase.__init__(self, case_root, infile)

    def set_value(self, item, value, subgroup=None, ignore_type=False):
        val = None
        # allow the user to set all instances of item if subgroup is not provided
        if subgroup is None:
            nodes = self.get_nodes("entry", {"id":item})
            for node in nodes:
                self._set_value(node, value, vid=item, ignore_type=ignore_type)
                val = value
        else:
            nodes = self.get_nodes("job", {"name":subgroup})
            for node in nodes:
                vnode = self.get_optional_node("entry", {"id":item}, root=node)
                if vnode is not None:
                    val = self._set_value(vnode, value, vid=item, ignore_type=ignore_type)

        return val

    def get_value(self, item, attribute={}, resolved=True, subgroup="run"):
        """
        Must default subgroup to something in order to provide single return value
        """
        value = None

        job_node = self.get_optional_node("job", {"name":subgroup})
        if job_node is not None:
            node = self.get_optional_node("entry", {"id":item}, root=job_node)
            if node is not None:
                value = self.get_resolved_value(node.get("value"))

                # Return value as right type if we were able to fully resolve
                # otherwise, we have to leave as string.
                if "$" not in value:
                    type_str = self._get_type_info(node)
                    value = convert_to_type(value, type_str, item)


        return value

    def get_values(self, item, attribute={}, resolved=True, subgroup=None):
        """Returns the value as a string of the first xml element with item as attribute value. 
        <elememt_name attribute='attribute_value>value</element_name>"""
        
        logger.debug("(get_values) Input values: %s , %s , %s , %s , %s" , self.__class__.__name__ , item, attribute, resolved, subgroup)      
                
        nodes   = [] # List of identified xml elements  
        results = [] # List of identified parameters 
       
        # Find all nodes with attribute name and attribute value item
        # xpath .//*[name='item']
        # for job in self.get_nodes("job") :    
        groups = self.get_nodes("group")
        
        for group in groups :
            
            roots = []
            jobs  = []
            jobs  = self.get_nodes("job" , root=group)
            
            if (len(jobs)) :
                roots = jobs
            else : 
                roots = [group]
            
            for r in roots :    
            
                if item :
                    nodes = self.get_nodes("entry",{"id" : item} , root=r )
                else :
                   # Return all nodes
                   nodes = self.get_nodes("entry" , root=r)
      
                # seach in all entry nodes
                for node in nodes:
                   
                    # Init and construct attribute path
                    attr      = None 
                    if (r.tag == "job") :
                        # make job part of attribute path
                        attr = r.get('name') + "/" + node.get('id')
                    else:
                         attr = node.get('id')
                         
                    # Build return structure     
                    g       = group.get('id')   
                    val     = node.get('value')
                    t       = self._get_type(node)
                    desc    = self._get_description(node)
                    default = super(EnvBase , self)._get_default(node)
                    file    = self.filename
    
                    v = { 'group' : g , 'attribute' : attr , 'value' : val , 'type' : t , 'description' : desc , 'default' : default , 'file' : file}
                    logger.debug("Found node with value for %s = %s" , item , v )   
                    results.append(v)
         
        logger.debug("(get_values) Return value:  %s" , results )
               
        return results

    def get_type_info(self, vid):
        nodes = self.get_nodes("entry",{"id":vid})
        type_info = None
        for node in nodes:
            new_type_info = self._get_type_info(node)
            if type_info is None:
                type_info = new_type_info
            else:
                expect( type_info == new_type_info,
                        "Inconsistent type_info for entry id=%s %s %s" % (vid, new_type_info, type_info))
        return type_info

    def get_jobs(self):
        result = []
        for node in self.get_nodes("job"):
            name = node.get("name")
            template = self.get_value("template", subgroup=name)
            task_count = self.get_value("task_count", subgroup=name)
            result.append((name, template, task_count))
        return result

    def create_job_groups(self, bjobs):
        # only the job_submission group is repeated
        group = self.get_node("group", {"id":"job_submission"})
        # look to see if any jobs are already defined
        cjobs = self.get_jobs()
        childnodes = list()

        expect(len(cjobs)==0," Looks like job groups have already been created")

        for child in reversed(group):
            childnodes.append(deepcopy(child))
            group.remove(child)

        for name,template,task_count in bjobs:
            newjob = ET.Element("job")
            newjob.set("name",name)
            template_node = ET.SubElement(newjob, "entry", {"id":"template","value":template})
            task_count_node  =  ET.SubElement(newjob, "entry", {"id":"task_count", "value":task_count})
            for node in (template_node, task_count_node):
                node = ET.SubElement(node, "type")
                node.text = "char"
            for child in childnodes:
                newjob.append(deepcopy(child))
            group.append(newjob)

