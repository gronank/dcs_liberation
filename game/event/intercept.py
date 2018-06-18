import math
import random

from dcs.task import *
from dcs.vehicles import *

from game import db
from game.operation.intercept import InterceptOperation
from userdata.debriefing import Debriefing

from .event import Event


class InterceptEvent(Event):
    BONUS_BASE = 5
    STRENGTH_INFLUENCE = 0.3
    GLOBAL_STRENGTH_INFLUENCE = 0.3
    AIRDEFENSE_COUNT = 3

    transport_unit = None  # type: FlyingType

    def __str__(self):
        return "Intercept from {} at {}".format(self.from_cp, self.to_cp)

    @property
    def threat_description(self):
        return "{} aircraft".format(self.enemy_cp.base.scramble_count())

    def is_successfull(self, debriefing: Debriefing):
        units_destroyed = debriefing.destroyed_units[self.defender_name].get(self.transport_unit, 0)
        if self.from_cp.captured:
            return units_destroyed > 0
        else:
            return units_destroyed == 0

    def commit(self, debriefing: Debriefing):
        super(InterceptEvent, self).commit(debriefing)

        if self.attacker_name == self.game.player:
            if self.is_successfull(debriefing):
                self.to_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)
            else:
                self.from_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)
        else:
            # enemy attacking
            if self.is_successfull(debriefing):
                self.from_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)
            else:
                self.to_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)

    def skip(self):
        if self.to_cp.captured:
            self.to_cp.base.affect_strength(-self.STRENGTH_INFLUENCE)

    def player_attacking(self, interceptors: db.PlaneDict, clients: db.PlaneDict):
        escort = self.to_cp.base.scramble_sweep()

        self.transport_unit = random.choice(db.find_unittype(Transport, self.defender_name))
        assert self.transport_unit is not None

        airdefense_unit = db.find_unittype(AirDefence, self.defender_name)[-1]
        op = InterceptOperation(game=self.game,
                                attacker_name=self.attacker_name,
                                defender_name=self.defender_name,
                                attacker_clients=clients,
                                defender_clients={},
                                from_cp=self.from_cp,
                                to_cp=self.to_cp)

        op.setup(escort=escort,
                 transport={self.transport_unit: 1},
                 airdefense={airdefense_unit: self.AIRDEFENSE_COUNT},
                 interceptors=interceptors)

        self.operation = op

    def player_defending(self, escort: db.PlaneDict, clients: db.PlaneDict):
        interceptors = self.from_cp.base.scramble_interceptors()

        self.transport_unit = random.choice(db.find_unittype(Transport, self.defender_name))
        assert self.transport_unit is not None

        op = InterceptOperation(game=self.game,
                                attacker_name=self.attacker_name,
                                defender_name=self.defender_name,
                                attacker_clients={},
                                defender_clients=clients,
                                from_cp=self.from_cp,
                                to_cp=self.to_cp)

        op.setup(escort=escort,
                 transport={self.transport_unit: 1},
                 interceptors=interceptors,
                 airdefense={})

        self.operation = op


