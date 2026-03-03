# -*- coding: utf-8 -*-
"""
Entidades de dominio puras. Sin dependencias externas.

***************************************************************************
    domain.py
    ---------------------
    Date                 : Marzo 2026
    Copyright            : (C) 2026 by Ingeniowares
    Email                : 
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Ingenioware                                                       *
*                                                                         *
***************************************************************************
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class ElementType(Enum):
    NODE = "node"
    PIPE = "pipe"
    TANK = "tank"
    RESERVOIR = "reservoir"
    PUMP = "pump"
    VALVE = "valve"


class NodeType(Enum):
    JUNCTION = "junction"
    TANK = "tank"
    RESERVOIR = "reservoir"


@dataclass
class Coordinate:
    x: float
    y: float
    z: float = 0.0
    
    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "z": self.z}
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Coordinate':
        return cls(x=data.get('x', 0.0), y=data.get('y', 0.0), z=data.get('z', 0.0))


@dataclass
class HydraulicElement:
    """Base para todos los elementos de red"""
    id: str
    element_type: ElementType
    geometry: Any  # WKT string o GeoJSON
    attributes: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    modified_at: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_geojson(self) -> dict:
        """Convierte a GeoJSON Feature"""
        return {
            "type": "Feature",
            "id": self.id,
            "geometry": self.geometry if isinstance(self.geometry, dict) else None,
            "properties": {
                **self.attributes,
                "_version": self.version,
                "_modified": self.modified_at.isoformat()
            }
        }


@dataclass 
class Node(HydraulicElement):
    elevation: float = 0.0
    base_demand: float = 0.0
    node_type: NodeType = NodeType.JUNCTION


@dataclass
class Pipe(HydraulicElement):
    start_node_id: str = ""
    end_node_id: str = ""
    length: float = 0.0
    diameter: float = 100.0  # mm
    roughness: float = 100.0  # C HW
    status: str = "OPEN"


@dataclass
class Project:
    """Agregado raíz"""
    id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    is_dirty: bool = False  # Cambios locales pendientes
    offline_created: bool = False
    elements: Dict[str, HydraulicElement] = field(default_factory=dict)
    
    def add_element(self, element: HydraulicElement):
        self.elements[element.id] = element
        self.modified_at = datetime.now()
        self.is_dirty = True
    
    def get_element(self, element_id: str) -> Optional[HydraulicElement]:
        return self.elements.get(element_id)
    
    def get_elements_by_type(self, element_type: ElementType) -> List[HydraulicElement]:
        return [e for e in self.elements.values() if e.element_type == element_type]
    
    def to_network_summary(self) -> dict:
        """Resumen para API"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "element_counts": {
                et.value: len(self.get_elements_by_type(et))
                for et in ElementType
            },
            "last_modified": self.modified_at.isoformat() if self.modified_at else None,
            "version": max((e.version for e in self.elements.values()), default=1)
        }


@dataclass
class SimulationConfig:
    """Configuración de simulación EPANET"""
    duration_hours: float = 24.0
    hydraulic_timestep: int = 3600  # segundos
    quality_timestep: int = 300
    pattern_timestep: int = 3600
    start_time: datetime = field(default_factory=datetime.now)
    report_timestep: int = 3600
    scenario_name: str = "Escenario Base"


@dataclass
class SimulationResult:
    """Resultados de nodo en un time-step"""
    timestamp: datetime
    node_id: str
    pressure: float  # mca
    head: float      # m
    demand: float    # L/s
    quality: float   # mg/L (opcional)