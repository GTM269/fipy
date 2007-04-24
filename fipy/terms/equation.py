#!/usr/bin/env python

## -*-Pyth-*-
 # ###################################################################
 #  FiPy - a finite volume PDE solver in Python
 # 
 #  FILE: "equation.py"
 #                                    created: 11/9/04 {11:51:08 AM} 
 #                                last update: 4/20/07 {11:33:09 AM} 
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #  Author: James Warren   <jwarren@nist.gov>
 #    mail: NIST
 #     www: http://www.ctcms.nist.gov/fipy/
 #  
 # ========================================================================
 # This document was prepared at the National Institute of Standards
 # and Technology by employees of the Federal Government in the course
 # of their official duties.  Pursuant to title 17 Section 105 of the
 # United States Code this document is not subject to copyright
 # protection and is in the public domain.  summationTerm.py
 # is an experimental work.  NIST assumes no responsibility whatsoever
 # for its use by other parties, and makes no guarantees, expressed
 # or implied, about its quality, reliability, or any other characteristic.
 # We would appreciate acknowledgement if the document is used.
 # 
 # This document can be redistributed and/or modified freely
 # provided that any derivative works bear some notice that they are
 # derived from it, and any modified versions bear some notice that
 # they have been modified.
 # ========================================================================
 #  See the file "license.terms" for information on usage and  redistribution of this file, and for a DISCLAIMER OF ALL WARRANTIES.
 #  
 #  Description: 
 # 
 #  History
 # 
 #  modified   by  rev reason
 #  ---------- --- --- -----------
 #  2004-11-09 JEG 1.0 original
 # ###################################################################
 ##

from fipy.terms.term import Term
from fipy.terms import TransientTerm, DiffusionTerm, \
  ExplicitDiffusionTerm, ImplicitSourceTerm
from fipy.terms.convectionTerm import ConvectionTerm
from fipy.terms.explicitSourceTerm import _ExplicitSourceTerm

class _Equation(Term):
    def __init__(self):
        self.orderedKeys = ["TransientTerm", "ExplicitDiffusionTerm", 
          "DiffusionTerm", "ConvectionTerm", "ImplicitSourceTerm", 
          "_ExplicitSourceTerm"]

        self.terms = {}
        
        for type in self.orderedKeys:
            self.terms[type] = None
	    
	Term.__init__(self)
	
    def copy(self):
        eq = _Equation()
        eq.terms = self.terms
        return eq
        
    def orderedPlusOtherKeys(self):
        return self.orderedKeys \
          + [k for k in self.terms.keys() if k not in self.orderedKeys]


    def _getDiffusiveGeomCoeff(self, mesh):
        if self.terms["DiffusionTerm"] is None:
            return None
        else:
            return self.terms["DiffusionTerm"]._getGeomCoeff(mesh)
        
    def _buildMatrix(self, var, boundaryConditions, dt, equation=None):
        from fipy.tools import numerix
        from fipy.tools.sparseMatrix import _SparseMatrix

        N = len(var)
        self.RHSvector = numerix.zeros((N,),'d')
        self.matrix = _SparseMatrix(size=N)

        for key in self.orderedPlusOtherKeys():
            term = self.terms[key]
            if term is not None:
                termMatrix, termRHSvector = term._buildMatrix(var, 
                                                              boundaryConditions, 
                                                              dt=dt, equation=self)

                self.matrix += termMatrix
                self.RHSvector += termRHSvector
	
        matrix = self.matrix
        RHSvector = self.RHSvector
        if not self._cacheMatrix:
            self.matrix = None
        if not self._cacheRHSvector:
            self.RHSvector = None
            
	return (matrix, RHSvector)
        
    def _getDefaultSolver(self, solver):
        for key in self.orderedPlusOtherKeys():
            term = self.terms[key]
            if term is not None:
                defaultsolver = term._getDefaultSolver(solver)
                if defaultsolver is not None:
                    return defaultsolver
                
        return solver

    def __repr__(self):
        reprs = []
        for key in self.orderedPlusOtherKeys():
            term = self.terms[key]
            if term is not None:
                reprs.append(repr(term))
                
        return " + ".join(reprs) + " == 0"

    def __add__(self, other):
        r"""
        Add a `Term` to another `Term`, number or variable.

           >>> Term(coeff=1.) + 10. + Term(2.)
           10.0 + Term(coeff=3.0) == 0
           >>> Term(coeff=1.) + Term(coeff=2.) + Term(coeff=3.)
           Term(coeff=6.0)

        """
        if self._otherIsZero(other):
            return self
        else:
            dup = self.copy()
            dup += other
                
            return dup
        
    def _appendTerm(self, other, key):
        if self.terms[key] is None:
            self.terms[key] = other
        else:
            self.terms[key] = self.terms[key] + other
        
    def __iadd__(self, other):
        if other is not None:
            if not isinstance(other, Term):
                self._appendTerm(_ExplicitSourceTerm(coeff=other), "_ExplicitSourceTerm")
            elif isinstance(other, _Equation):
                for key in other.terms.keys():
                    self += other.terms[key]
            else:
                appended = False
                for key in self.terms.keys():
                    if eval("isinstance(other, %s)" % key):
                        self._appendTerm(other, key)
                        appended = True
                        break
                        
                if not appended:
                    self.terms[other.__class__.__name__] = other
        
        return self
        
    def __neg__(self):
        r"""
         Negate a `Term`.

           >>> -(Term(coeff=1.) - Term(coeff=2.))
           Term(coeff=1.0)

        """
        dup = self.copy()
        
        for key, term in self.terms.iteritems():
            if term is not None:
                dup.terms[key] = -term
                
        return dup

def _test(): 
    import doctest
    return doctest.testmod()

if __name__ == "__main__":
    _test()

