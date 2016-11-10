#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Created on Sep 13, 2016

@author: brian
'''

from __future__ import division, absolute_import

from warnings import warn
import pandas as pd
import numpy as np

from traits.api import (HasStrictTraits, Str, List, Constant, provides, 
                        Callable, CStr, Tuple)

import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class TransformStatisticOp(HasStrictTraits):
    """
    Apply a function to a statistic, creating a new statistic.  The function can
    be applied to the entire statistic, or it can be applied individually to groups
    of the statistic.  The function should take a `pandas.Series` as its only argument.
    Return type is arbitrary, but a `float` or a `pandas.Series` is most common.

    Attributes
    ----------
    name : Str
        The operation name.  Becomes the first element in the
        Experiment.statistics key tuple.
    
    statistic : Tuple(Str, Str)
        The statistic to apply the function to.
        
    function : Callable
        The function used to transform the statistic.  `function` must take a 
        Series as its only parameter.  The return type is arbitrary, but a `float`
        or a `pandas.Series` is most common.  If `statistic_name` is unset, the name 
        of the function becomes the second in element in the Experiment.statistics key tuple.
        
    statistic_name : Str
        The name of the function; if present, becomes the second element in
        the Experiment.statistics key tuple.
        
    by : List(Str)
        A list of metadata attributes to aggregate the data before applying the
        function.  For example, if the experiment has two pieces of metadata,
        `Time` and `Dox`, setting `by = ["Time", "Dox"]` will apply `function` 
        separately to each subset of the data with a unique combination of
        `Time` and `Dox`.
   
    Examples
    --------
    
    >>> stats_op = ChannelStatisticOp(name = "Mean",
    ...                               channel = "Y2-A",
    ...                               function = np.mean,
    ...                               by = ["Dox"])
    >>> ex2 = stats_op.apply(ex)
    >>> log_op = TransformStatisticOp(name = "LogMean",
    ...                               statistic = ("Mean", "mean"),
    ...                               function = np.log)
    >>> ex3 = log_op.apply(ex2)  
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.statistics')
    friendly_id = Constant("Statistics")
    
    name = CStr()
    statistic = Tuple(Str, Str)
    function = Callable()
    statistic_name = Str()
    by = List(Str)
    
    def apply(self, experiment):
        """
        Estimate the Gaussian mixture model parameters
        """
        
        if not experiment:
            raise util.CytoflowOpError("Must specify an experiment")

        if not self.name:
            raise util.CytoflowOpError("Must specify a name")
        
        if not self.statistic:
            raise util.CytoflowOpError("Must specify a statistic")

        if not self.function:
            raise util.CytoflowOpError("Must specify a function")

        if self.statistic not in experiment.statistics:
            raise util.CytoflowOpError("Statistic {0} not found in the experiment"
                                  .format(self.channel))

        if not self.by:
            raise util.CytoflowOpError("Must specify some grouping conditions "
                                       "in 'by'")
       
        for b in self.by:
            if b not in experiment.data:
                raise util.CytoflowOpError("Aggregation metadata {0} not found"
                                      " in the experiment"
                                      .format(b))
            if len(experiment.data[b].unique()) > 100: #WARNING - magic number
                raise util.CytoflowOpError("More than 100 unique values found for"
                                      " aggregation metadata {0}.  Did you"
                                      " accidentally specify a data channel?"
                                      .format(b))
                
        old_stat = experiment.statistics[self.statistic]
        data = old_stat.reset_index()
        
        idx = pd.MultiIndex.from_product([data[x].unique() for x in self.by], 
                                         names = self.by)
        new_stat = pd.Series(index = idx, dtype = np.dtype(object))
        
        for group in data[self.by].itertuples(index = False):
            group = list(group)
            s = old_stat.xs(group, level = self.by)
            
            try:
                x = self.function(s)
            except Exception as e:
                raise util.CytoflowOpError("Your function through an error: {}"
                                      .format(e))
                
            print x
            new_stat.loc[group] = x
            print new_stat
        
        
        
#         groupby = old_stat.reset_index().groupby(self.by)

#         for group, data_subset in groupby:
#             if len(data_subset) == 0:
#                 warn("Group {} had no data"
#                      .format(group), 
#                      util.CytoflowOpWarning)
                
#         idx = pd.MultiIndex(levels = [[]] * len(self.by), 
#                             labels = [[]] * len(self.by), 
#                             names = self.by)

#         
#         for group, _ in groupby:
#             print group
#             print old_stat.xs(list(group), level = self.by)
#             try:
#                 print data_subset
#                 print "---"
#                 x = self.function(data_subset[0])
#                 print x
#                 print "-----------"
#                 new_stat[group] = x
#             except Exception as e:
#                 raise util.CytoflowOpError("Your function through an error: {}"
#                                       .format(e))
                
        # special handling for lists
        if type(new_stat.iloc[0]) is pd.Series:
            new_stat = pd.concat(new_stat.to_dict(), names = self.by + new_stat.iloc[0].index.names)
        
        new_experiment = experiment.clone()
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        if self.statistic_name:
            new_experiment.statistics[(self.name, self.statistic_name)] = new_stat
        else:
            new_experiment.statistics[(self.name, self.function.__name__)] = new_stat

        
        return new_experiment
