"""
QMHub
A universal QM/MM interface.
"""

from .simulation import Simulation
from .model import Model
from .engine import Engine
from .iotools import load_system, return_results


class QMMM(object):
    def __init__(self, driver=None):
        self.driver = driver
        self.engine_groups = {}

    def setup_simulation(self, protocol="md", **kwargs):
        self.simulation = Simulation(protocol, **kwargs)

    def load_system(self, input, mode):
        self.system = load_system(mode)(input, simulation=self.simulation)

    def build_model(self, switching_type=None, cutoff=None, swdist=None, pbc=None):
        if not hasattr(self, 'system'):
            raise AttributeError("Please load system first.")

        self.model = Model(
            self.system.qm.atoms.positions,
            self.system.atoms.positions,
            self.system.qm.atoms.charges,
            self.system.atoms.charges,
            self.system.cell_basis,
            self.system.qm_charge,
            switching_type=switching_type,
            cutoff=cutoff,
            swdist=swdist,
            pbc=pbc
        )

    def add_engine(self, engine, name=None, group_name=None, basedir=None, keywords=None):
        if name is None:
            name = engine

        if group_name is None:
            group_name = "engine"

        if not hasattr(self, group_name):
            group_obj = Engine(
                self.system.qm.atoms.positions,
                self.system.qm.atoms.elements,
                self.model.elec.embedding_mm_positions,
                self.model.elec.embedding_mm_charges,
                charge=self.system.qm_charge,
                mult=self.system.qm_mult,
            )
            setattr(self, group_name, group_obj)
            self.engine_groups[group_name] = group_obj

            self.model.get_result(
                name=group_name,
                qm_energy=group_obj.qm_energy,
                qm_energy_gradient=group_obj.qm_energy_gradient,
                mm_esp=group_obj.mm_esp,
            )

            result_obj = getattr(self.model, group_name)
            self.simulation.add_engine(group_name, result_obj)

        group_obj = self.engine_groups[group_name]
        group_obj.add_engine(engine, name=name, basedir=basedir, keywords=keywords)

    def return_results(self, output, mode):
        energy, energy_gradient = self.simulation.return_results()
        return_results(mode)(output, energy, energy_gradient)
