'''
Name:        definitionQueryLayersFromAttribute
Purpose:     Create a layer for each unique permutation of a specified attribute
             field.

Author:      Joel McCune (knu2xs@gmail.com)

Created:     04Mar2013
Copyright:   (c) Joel McCune 2013
Licence:
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    The GNU General Public License can be found at
    <http://www.gnu.org/licenses>.
'''

# import modules
import arcpy
import os

# return set containing unique permutations of specified field values
def getValueList(inputTable, field):

    # use search cursor to return list of all field values
    values=[row[0] for row in arcpy.da.SearchCursor(inputTable, (field))]

    # create set from list, containing only unique permutations
    uniqueValues=set(values)

    # return sorted set of unique value permutations
    return sorted(uniqueValues)

# create temporary layer to use as template for other layers
def createTempLayer(sourceFC):

    # create an in memory feature layer
    tempLayer=arcpy.MakeFeatureLayer_management(in_features=sourceFC,
        out_layer='tempLayer').getOutput(0)

    # full path to layer in scratch folder
    outputLayer=os.path.join(arcpy.env.scratchFolder, "tempLayer.lyr")

    # save the layer file to the temp directory
    arcpy.SaveToLayerFile_management(tempLayer, outputLayer)

    # return path to temp directory
    return outputLayer

# create definition query
def createQueryString(inputWorkspace, attributeField, inputValue):

    # return a field name with proper field delimiters for workspace type
    attributeString = arcpy.AddFieldDelimiters(inputWorkspace, attributeField)

    # create definition query string based on numbers versus text input
    if type(inputValue) == int or type(inputValue) == float:

        # convert numeric to string for concantenation
        defString = str(inputValue)

    else:

        # escape any possible ' characters so SQL query works
        inputValue = inputValue.replace("'", "''")

        # strings need to be surrounded by single quotes
        defString="'"+inputValue+"'"

    # assemble and return SQL query string
    return (attributeString+"="+defString)

def main(inputFC, field):

    # overwrite output
    arcpy.env.overwriteOutput = True

    # create memory layer for dissolve input
    inputFeatureLayer=arcpy.MakeFeatureLayer_management(inputFC,
        "inputFeatureLayer")

    # set map to current map document
    mxd = arcpy.mapping.MapDocument("CURRENT")

    # set dataframe to first in map
    dataFrame=arcpy.mapping.ListDataFrames(mxd)[0]

    # create temp layer as template
    tempDir=arcpy.env.scratchFolder
    tempLayer=createTempLayer(inputFC)

    # get list of every unique permutation of attribute
    values=getValueList(inputFC, field)

    # create unique layer for every permutation of attribute value
    for value in values:

        # create layer object from outputFC layer file
        newLayer=arcpy.mapping.Layer(tempLayer)

        # get workspace path for layer
        layerWorkspace=newLayer.workspacePath

        # create definition query for this permutation of attribute values
        newLayer.definitionQuery=createQueryString(layerWorkspace, field, value)

        # change layer name to reflect this permutation of attribute values
        if value == "" or value == " ":
            newLayer.name = "No Value"
        else:
            newLayer.name = str(value)

        # add the layer to the data frame at the bottom of the table of contents
        arcpy.mapping.AddLayer(dataFrame, newLayer, "BOTTOM")

        # delete the layer object for next iteration
        del newLayer

    # remove temporary directory
    arcpy.Delete_management(arcpy.env.scratchFolder)

if __name__ == '__main__':

    # collect arguments
    inputFeatureClass=arcpy.GetParameterAsText(0) # input dataset
    queryField=arcpy.GetParameterAsText(1) # definition query field

    main(inputFeatureClass, queryField)
