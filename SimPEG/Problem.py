import Utils, Survey, numpy as np, scipy.sparse as sp
import Model

class BaseProblem(object):
    """
        Problem is the base class for all geophysical forward problems in SimPEG.


        The problem is a partial differential equation of the form:

        .. math::
            c(m, u) = 0

        Here, m is the model and u is the field (or fields).
        Given the model, m, we can calculate the fields u(m),
        however, the data we collect is a subset of the fields,
        and can be defined by a linear projection, P.

        .. math::
            d_\\text{pred} = Pu(m)

        We are interested in how changing the model transforms the data,
        as such we can take write the Taylor expansion:

        .. math::
            Pu(m + hv) = Pu(m) + hP\\frac{\partial u(m)}{\partial m} v + \mathcal{O}(h^2 \left\| v \\right\| )

        We can linearize and define the sensitivity matrix as:

        .. math::
            J = P\\frac{\partial u}{\partial m}

        The sensitivity matrix, and it's transpose will be used in the inverse problem
        to (locally) find how model parameters change the data, and optimize!
    """

    __metaclass__ = Utils.SimPEGMetaClass

    counter = None   #: A SimPEG.Utils.Counter object

    surveyPair = Survey.BaseSurvey
    modelPair = Model.BaseModel

    def __init__(self, model, **kwargs):
        Utils.setKwargs(self, **kwargs)
        assert (isinstance(model, self.modelPair) or
            isinstance(model, Model.ComboModel) and isinstance(model.models[0], self.modelPair)
            ), "Model object must be an instance of a %s class."%(self.modelPair.__name__)
        self.model = model

    @property
    def mesh(self): return self.model.mesh

    @property
    def survey(self):
        """
        The survey object for this problem.
        """
        return getattr(self, '_survey', None)

    def pair(self, d):
        """Bind a survey to this problem instance using pointers."""
        assert isinstance(d, self.surveyPair), "Data object must be an instance of a %s class."%(self.surveyPair.__name__)
        if d.ispaired:
            raise Exception("The survey object is already paired to a problem. Use survey.unpair()")
        self._survey = d
        d._prob = self

    def unpair(self):
        """Unbind a survey from this problem instance."""
        if not self.ispaired: return
        self.survey._prob = None
        self._survey = None

    @property
    def ispaired(self): return self.survey is not None

    @Utils.timeIt
    def Jvec(self, m, v, u=None):
        """
            :param numpy.array m: model
            :param numpy.array v: vector to multiply
            :param numpy.array u: fields
            :rtype: numpy.array
            :return: Jv

            Working with the general PDE, c(m, u) = 0, where m is the model and u is the field,
            the sensitivity is defined as:

            .. math::
                J = P\\frac{\partial u}{\partial m}

            We can take the derivative of the PDE:

            .. math::
                \\nabla_m c(m, u) \delta m + \\nabla_u c(m, u) \delta u = 0

            If the forward problem is invertible, then we can rearrange for du/dm:

            .. math::
                J = - P \left( \\nabla_u c(m, u) \\right)^{-1} \\nabla_m c(m, u)

            This can often be computed given a vector (i.e. J(v)) rather than stored, as J is a large dense matrix.

        """
        raise NotImplementedError('J is not yet implemented.')

    @Utils.timeIt
    def Jtvec(self, m, v, u=None):
        """
            :param numpy.array m: model
            :param numpy.array v: vector to multiply
            :param numpy.array u: fields
            :rtype: numpy.array
            :return: JTv

            Effect of transpose of J on a vector v.
        """
        raise NotImplementedError('Jt is not yet implemented.')


    @Utils.timeIt
    def Jvec_approx(self, m, v, u=None):
        """

            :param numpy.array m: model
            :param numpy.array v: vector to multiply
            :param numpy.array u: fields
            :rtype: numpy.array
            :return: Jv

            Approximate effect of J on a vector v

        """
        return self.Jvec(m, v, u)

    @Utils.timeIt
    def Jtvec_approx(self, m, v, u=None):
        """
            :param numpy.array m: model
            :param numpy.array v: vector to multiply
            :param numpy.array u: fields
            :rtype: numpy.array
            :return: JTv

            Approximate transpose of J*v

        """
        return self.Jtvec(m, v, u)

    def fields(self, m):
        """
            The field given the model.

            .. math::
                u(m)

        """
        pass

    #TODO: Rename and refactor to createSyntheticData
    def createSyntheticSurvey(self, m, std=0.05, u=None, **geometry_kwargs):
        """
            Create synthetic survey given a model, and a standard deviation.

            :param numpy.array m: geophysical model
            :param numpy.array std: standard deviation
            :rtype: SurveyObject
            :return: survey

            Returns the observed data with random Gaussian noise
            and Wd which is the same size as data, and can be used to weight the inversion.
        """
        survey = self.surveyPair(mtrue=m, **geometry_kwargs)
        survey.pair(self)
        survey.dtrue = survey.dpred(m, u=u)
        noise = std*abs(survey.dtrue)*np.random.randn(*survey.dtrue.shape)
        survey.dobs = survey.dtrue+noise
        survey.std = survey.dobs*0 + std
        return survey



