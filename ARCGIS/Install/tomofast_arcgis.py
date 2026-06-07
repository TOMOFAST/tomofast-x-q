# -*- coding: utf-8 -*-
from tomofast_arcgis_base import TomofastArcGISBase
from tomofast_arcgis_data import DataMixin
from tomofast_arcgis_mesh import MeshMixin
from tomofast_arcgis_params import ParamsMixin
from tomofast_arcgis_run import RunMixin


class TomofastArcGIS(RunMixin, ParamsMixin, MeshMixin, DataMixin, TomofastArcGISBase):
    pass