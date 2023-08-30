from typing import ClassVar, Mapping, Sequence, Optional, cast, Tuple, List, Any, Dict

from typing_extensions import Self

from viam.module.types import Reconfigurable
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName, ResponseMetadata, Geometry
from viam.components.camera import Camera
from viam.resource.types import Model, ModelFamily
from viam.resource.base import ResourceBase
from viam.media.video import NamedImage
from PIL import Image
from viam.errors import NoCaptureToStoreError
from viam.services.vision import Vision

class ColorFilterCam(Camera, Reconfigurable):
    # A ColorFilterCam wraps the underlying camera `actualCam` and only keeps the data captured on the actual camera if `visionService`
    # detects a certain color in the captured image.
    MODEL: ClassVar[Model] = Model(ModelFamily("example", "camera"), "colorfilter")

    def __init__(self, name: str):
        super().__init__(name)

    # Constructor
    @classmethod
    def new_cam(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        cam = cls(config.name)
        cam.reconfigure(config, dependencies)
        return cam

    # Validates JSON Configuration
    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        actual_cam = config.attributes.fields["actual_cam"].string_value
        if actual_cam == "":
            raise Exception("actual_cam attribute is required for a ColorFilterCam component")
        vision_service = config.attributes.fields["vision_service"].string_value
        if vision_service == "":
            raise Exception("vision_service attribute is required for a ColorFilterCam component")
        return [actual_cam, vision_service]

    # Handles attribute reconfiguration
    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        actual_cam_name = config.attributes.fields["actual_cam"].string_value
        actual_cam = dependencies[Camera.get_resource_name(actual_cam_name)]
        self.actual_cam = cast(Camera, actual_cam)

        vision_service_name = config.attributes.fields["vision_service"].string_value
        vision_service = dependencies[Vision.get_resource_name(vision_service_name)]
        self.vision_service = cast(Vision, vision_service)

    # Returns details about the camera
    async def get_properties(self, *, timeout: Optional[float] = None, **kwargs) -> Camera.Properties:
        return await self.actual_cam.get_properties()

    # Filters the output of the underlying camera
    async def get_image(self, mime_type: str = "", *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs) -> Image.Image:
        if extra and extra["fromDataManagement"]:
            img = await self.actual_cam.get_image()
            detections = await self.vision_service.get_detections(img)
            if len(detections) > 0:
                return img
            raise NoCaptureToStoreError()
        
        return await self.actual_cam.get_image()

    # get_images: unimplemented
    async def get_images(self, *, timeout: Optional[float] = None, **kwargs) -> Tuple[List[NamedImage], ResponseMetadata]:
        raise NotImplementedError

    # get_point_cloud: unimplemented
    async def get_point_cloud(self, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs) -> Tuple[bytes, str]:
        raise NotImplementedError
    
    # get_geometries: unimplemented
    async def get_geometries(self) -> List[Geometry]:
        raise NotImplementedError
