from .core import BasePayload


# noinspection PyPep8Naming
class LeftoverPayload(BasePayload):

    def __init__(self, **kwargs):
        super(LeftoverPayload, self).__init__(**kwargs)
        self.type = kwargs.get('type', 'Leftover')
        self.partName = kwargs.get('partName', '')
        self.material = kwargs.get('material', '')
        self.length = kwargs.get('length', -1)
        self.width = kwargs.get('width', -1)
        self.thickness = kwargs.get('thickness', -1)
        self.dimension = kwargs.get('dimension', '')
        self.observation = kwargs.get("observation", "")
        self.weight = kwargs.get("weight", -1)
        self.image = kwargs.get("image", "")
        self.location_x = kwargs.get("location_x", "")
        self.location_y = kwargs.get("location_y", "")

    @property
    def dimension(self) -> str:
        return self._dimension
    
    @dimension.setter
    def dimension(self, dimension: str) -> None:
        self._dimension = dimension

    @property
    def location_x(self) -> str:
        return self._location_x

    @location_x.setter
    def location_x(self, location_x: str) -> None:
        self._location_x = location_x

    @property
    def location_y(self) -> str:
        return self._location_y

    @location_y.setter
    def location_y(self, location_y: str) -> None:
        self._location_y = location_y

    @property
    def image(self) -> str:
        return self._image

    @image.setter
    def image(self, image: str) -> None:
        self._image = image

    @property
    def weight(self) -> float:
        return self._weight

    @weight.setter
    def weight(self, weight: float) -> None:
        self._weight = weight

    @property
    def observation(self) -> str:
        return self._observation

    @observation.setter
    def observation(self, observation: str) -> None:
        self._observation = observation

    @property
    def thickness(self) -> float:
        return self._thickness

    @thickness.setter
    def thickness(self, thickness: float) -> None:
        self._thickness = thickness

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, width: float) -> None:
        self._width = width

    @property
    def length(self) -> float:
        return self._length

    @length.setter
    def length(self, length: float) -> None:
        self._length = length

    @property
    def partName(self) -> str:
        return self._partName

    @partName.setter
    def partName(self, partName: str) -> None:
        self._partName = partName

    @property
    def material(self) -> str:
        return self._material

    @material.setter
    def material(self, material: str) -> None:
        self._material = material
