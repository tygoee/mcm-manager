from typing import Literal
import _typecls

SizeSystem = list[tuple[int, str | tuple[str, str]]]
Side = Literal['client', 'server']
Minecraft = _typecls.Minecraft
CFMedia = _typecls.CFMedia
PMMedia = _typecls.PMMedia
MRMedia = _typecls.MRMedia
URLMedia = _typecls.URLMedia
Media = _typecls.Media
MediaList = list[Media]
Manifest = _typecls.Manifest
Answers = _typecls.Answers
