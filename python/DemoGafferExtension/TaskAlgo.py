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
def retriveRelevantFiles(plug):
    def traverseNodes(node, upstreamNodes, sourceFiles):
        """ Traverse nodes to collect values from "fileName" attribute.

        :param node: plug/node instance
        """
        # traverse input plug
        for sourcePlug in node.children(Gaffer.Plug):
            # get input plugs from current node
            if sourcePlug.direction() != Gaffer.Plug.Direction.In:
                continue

            # Get source file from fileName
            if sourcePlug.children():
                for cPlug in sourcePlug.children():
                    traverseNodes(cPlug, upstreamNodes, sourceFiles)
            elif sourcePlug.getName() == 'fileName':
                if sourcePlug.getName() not in sourceFiles:
                    sourceFile = getFullPath(sourcePlug.getValue())
                    sourceFiles.add(os.path.expandvars(sourceFile))

            # Get upstream nodes
            if sourcePlug.getInput():
                upNode = sourcePlug.source().parent()
                if upNode not in upstreamNodes:
                    upstreamNodes.append(upNode)
                    traverseNodes(upNode, upstreamNodes, sourceFiles)
            else:
                traverseNodes(sourcePlug, upstreamNodes, sourceFiles)

    upstreamNode = plug.getInput().node()
    # Save all upstream node, for checking purpose if we
    # collected all upsteam nodes
    upstreamNodes = [upstreamNode]
    sourceFiles = set()

    # collect source files
    traverseNodes(upstreamNode, upstreamNodes, sourceFiles)
    return sourceFiles


def getFullPath(sourceFile, skipVariables=None):
    skipVariables = skipVariables if skipVariables else []
    pattern = re.compile(r'[$][{](.*?)[}]', re.S)
    scriptVariables = re.findall(pattern, sourceFile)
    if not scriptVariables:
        return sourceFile
    for scriptV in scriptVariables:
        if scriptV in skipVariables:
            continue
        # TODO: There should be a better way to get all values from script variables
        try:
            scriptVariableValue = root.context()[scriptV]
        except:
            skipVariables.append(scriptV)
            scriptVariableValue = '${{{}}}'.format(scriptV)

        pathWithoutScriptV = sourceFile.replace('${{{}}}'.format(scriptV), scriptVariableValue)
        return getFullPath(pathWithoutScriptV, skipVariables)
    return sourceFile
