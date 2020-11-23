##########################################################################
#
#  Copyright (c) 2020, John Haddon. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import os
import re

import Gaffer


## Creates a custom Gaffer extension to locate all
# the source files that might be relevant to a given
# output TaskPlug.
def retrive_relevant_files(plug):
    def traverse_nodes(node, upstream_nodes, source_files):
        """ Traverse nodes to collect values from "fileName" attribute.

        :param node: plug/node instance
        """
        # traverse input plug
        for source_plug_t in node.children(Gaffer.Plug):
            # get input plugs from current node
            if source_plug_t.direction() != Gaffer.Plug.Direction.In:
                continue

            # Get source file from fileName
            if source_plug_t.children():
                for c_plug in source_plug_t.children():
                    traverse_nodes(c_plug, upstream_nodes, source_files)
            elif source_plug_t.getName() == 'fileName':
                if source_plug_t.getName() not in source_files:
                    source_file = get_full_path(source_plug_t.getValue())
                    source_files.add(os.path.expandvars(source_file))

            # Get upstream nodes
            if source_plug_t.getInput():
                up_node = source_plug_t.source().parent()
                if up_node not in upstream_nodes:
                    upstream_nodes.append(up_node)
                    traverse_nodes(up_node, upstream_nodes, source_files)
            else:
                traverse_nodes(source_plug_t, upstream_nodes, source_files)

    upstream_node = plug.getInput().node()
    # Save all upstream node, for checking purpose if we
    # collected all upsteam nodes
    upstream_nodes = [upstream_node]
    source_files = set()

    # collect source_files
    traverse_nodes(upstream_node, upstream_nodes, source_files)
    return source_files


def get_full_path(source_file, skip_variables=None):
    skip_variables = skip_variables if skip_variables else []
    pattern = re.compile(r'[$][{](.*?)[}]', re.S)
    script_variables = re.findall(pattern, source_file)
    if not script_variables:
        return source_file
    for script_v in script_variables:
        if script_v in skip_variables:
            continue
        # TODO: There should be a better way to get all values from script variables
        try:
            script_v_value = root.context()[script_v]
        except:
            skip_variables.append(script_v)
            script_v_value = '${{{}}}'.format(script_v)

        dir_without_script_v = source_file.replace('${{{}}}'.format(script_v), script_v_value)
        return get_full_path(dir_without_script_v, skip_variables)
    return source_file


