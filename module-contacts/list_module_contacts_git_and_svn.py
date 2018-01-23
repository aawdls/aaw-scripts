#!/bin/env dls-python
"""
A script to list support modules in SVN and Git with their module contacts
and number of IOCs in which they appear as a direct dependency.
Writes an HTMl file.

:author Andrew Wilson
:date January 2018
"""
import os, logging, shutil
from pkg_resources import require
require("dls_ade")
require("dls_environment")
require("dls_dependency_tree")

from dls_ade import Server
from dls_environment.svn import svnClient, pysvn
import dls_environment
import dls_dependency_tree
import argparse

import module_contacts_html_template as html

def get_git_module_list(git_server, area):
    """
    Get a list of modules on the git server

    :param git_server(Server object): Git server object
    :param source(str): Suffix of URL to list from
    :return git_server_list (list)
    """
    logging.debug("Get dev_area_path")
    source = git_server.dev_area_path(area)
    logging.debug("Get server repo list")
    split_list = git_server.get_server_repo_list()

    git_module_list = []
    for module_path in split_list:
        if module_path.startswith(source + '/'):
            # Split module path by slashes twice and print what remains
            # after that, i.e. after 'controls/<area>/'
            module_name = module_path.split('/', 2)[-1]
            git_module_list.append(module_name)
    return git_module_list

def get_svn_module_list(svn_server, area):
    """
    Get a list of modules in <area> of SVN

    :param svn_server: SVN server object
    :param area: area of the repository to list
    :return: svn_module list, list of modules in area
    """
    logging.debug("svn.devArea")
    source = svn_server.devArea("support")
    # print the modules
    logging.debug("Get list of modules in %s area of SVN:" % area)
    assert svn_server.pathcheck(source), source + " does not exist in the repository"
    svn_module_list = []
    for node, _ in svn_server.list(source, depth=pysvn.depth.immediates)[1:]:
        module_name = os.path.basename(node.path)
        svn_module_list.append(module_name)
    return svn_module_list

class SupportModule():
    def __init__(self, module_name, in_git=False, in_svn=False, area="support"):
        self.module_name = module_name
        self.in_git = in_git
        self.in_svn = in_svn
        self.contact = ""
        self.cc = ""
        self.area = area
        self.has_git_contact = False
        self.has_svn_contact = False

    def get_module_name(self):
        return self.module_name

    def get_svn_module_contact(self, svn_server):
        """Return module contact and CC for an SVN module"""
        path = svn_server.devModule(self.module_name, self.area)
        contact = svn_server.propget("dls:contact", path)
        # contact is a dictionary of contacts associated with path and its files
        # and subdirectories. We're only interested in the properties on the top
        # directory (i.e. path).
        if contact and path in contact.keys():
            contact = contact[path]
        else:
            contact = "unspecified"
        cc = svn_server.propget("dls:cc", path)
        if cc and path in cc.keys():
            cc = cc[path]
        else:
            cc = "unspecified"

        # Is it really something?
        self.has_svn_contact = looks_like_real_contact(contact)

        # Store
        self.contact = contact
        self.cc = cc
        return contact.strip(), cc.strip()

    def get_git_module_contact(self, git_server):
        """Return module contact and CC for a git module"""
        source = git_server.dev_module_path(self.module_name, self.area)
        vcs = git_server.temp_clone(source)

        # Retrieve contact info
        try:
            contact = vcs.repo.git.check_attr(
                "module-contact", ".").split(' ')[-1]
            cc_contact = vcs.repo.git.check_attr(
                "module-cc", ".").split(' ')[-1]
        except:
            logging.warning("Exception from git contact check of %s")
            self.contact = "unspecified"
            self.cc = "unspecified"
            self.has_git_contact = False
        else:
            # Store
            self.contact = contact
            self.cc = cc_contact

            # Is it really something?
            self.has_git_contact = looks_like_real_contact(contact)

        finally:
            # Delete local clone
            shutil.rmtree(vcs.repo.working_tree_dir)

        return contact, cc_contact

    def get_vcs(self):
        vcs = []
        if self.in_git:
            vcs.append("Git")
        if self.in_svn:
            vcs.append("SVN")
        return ", ".join(vcs)

def looks_like_real_contact(input_str):
    """Return True if input_str looks like a contact"""
    if input_str.lower().strip() in ["", "unspecified"]:
        return False
    else:
        return True

def count_up_IOC_dependencies():
    """Count occurences of support modules in dependency tress of IOCs in redirector

    :return IOC_dependency(dict) key: module name, value: count of occurrences"""

    startup_files = dict(
        [line.split() for line in os.popen('configure-ioc list')])

    IOC_dependency = {}

    logging.debug("Counting up support modules depended on by IOCs")
    # Get dependency tree for each IOC
    total_number_IOCs = len(startup_files.keys())
    debug_counter = 0
    for ioc in startup_files.keys():

        debug_counter += 1
        # Some basic filters
        if ioc.startswith("BL") \
                and "-PS-" not in ioc and "BL-" not in ioc and "BL01B" not in ioc \
                and "-SIM-" not in ioc and "sim" not in ioc:

            # Get dependency tree for this IOC
            logging.debug("ioc %s (%d of %d)" % (ioc, debug_counter, total_number_IOCs))
            path = "/".join(startup_files[ioc].split("/")[:-3])
            tree = dls_dependency_tree.dependency_tree(None, module_path=path)
            if tree.name and tree.name != "BLInterface" and tree.name != "ioc":
                for leaf in tree.leaves:
                    ss_ioc_name = tree.name
                    ss_module = leaf.name
                    ss_version = leaf.version

                    # For each module, increment the counter
                    if ss_module in IOC_dependency:
                        IOC_dependency[ss_module] += 1
                    else:
                        IOC_dependency[ss_module] = 1

    return IOC_dependency

def parse_arguments():
    """Parse command line arguments"""
    help = """Write an HTML file with a list of support modules
        in SVN and git, with their module contacts and the number
        of IOCs in which they are direct dependencies."""
    argument_parser = argparse.ArgumentParser(description=help)
    argument_parser.add_argument("output_filename", type=str,
                                 help="Path to output HTML file")
    args = argument_parser.parse_args()
    return args

def main():

    args = parse_arguments()


    logging.basicConfig(level=logging.DEBUG)
    area = "support"
    logging.debug("Output HTML will be written to %s" % args.output_filename)

    # Git module list
    logging.debug("Getting list of Modules in %s area of git" % area)
    git_server = Server()
    git_module_list = get_git_module_list(git_server, area)

    # SVN module list
    logging.debug("Get list of modules in %s area of SVN." % area)
    logging.debug("svnclient")
    svn_server = svnClient()
    svn_module_list = get_svn_module_list(svn_server, area)

    # Combining the lists, creating objects
    module_list = []
    for module_name in git_module_list:
        also_in_svn = False
        # Check if also in SVN
        if module_name in svn_module_list:
            also_in_svn = True
            # Don't duplicate if so
            svn_module_list.remove(module_name)

        module_list.append(SupportModule(module_name, in_git=True, in_svn=also_in_svn, area=area))

    # The rest of the modules which don't have a git counterpart
    for module_name in svn_module_list:
        module_list.append(SupportModule(module_name, in_svn=True, area=area))

    # Sorting the combined list
    logging.debug("Sorting list")
    module_list = sorted(module_list, key=lambda obj: obj.get_module_name())

    # Look for occurrences in IOCs
    logging.debug("Getting list of IOCs in redirector")
    IOC_dependency = count_up_IOC_dependencies()

    # Simple display of results
    row_counter = 0
    with open(args.output_filename, "wb") as output_file:

        logging.debug("Printing HTML header...")
        output_file.write(html.page_head)
        output_file.write(html.body_start)
        output_file.write(html.table_head)

        logging.debug("Getting module contacts...")
        number_of_rows = len(module_list)

        for this_module in module_list:

            row_counter += 1
            module_name = this_module.get_module_name()

            # Retrieve count of IOCs it appears in
            if module_name in IOC_dependency:
                number_of_IOCs = IOC_dependency[module_name]
            else:
                number_of_IOCs = 0

            logging.debug("Processing module %d of %d (%s) which appears in %d IOCs" %(row_counter, number_of_rows, module_name, number_of_IOCs))

            # Get module contact
            # Use the SVN one if exists in both and not set in git
            if this_module.in_git:
                contact, cc = this_module.get_git_module_contact(git_server)
            if this_module.in_svn and not this_module.has_git_contact:
                contact, cc = this_module.get_svn_module_contact(svn_server)

            # Write a row of output
            output_file.write(html.one_row % (this_module.module_name, this_module.get_vcs(), contact, cc, number_of_IOCs))
            output_file.flush()

        logging.debug("Printing HTML footer")
        output_file.write(html.table_bottom)
        output_file.write(html.page_end)

        logging.debug("Script finished.")

if __name__ == "__main__":
    main()