"""
Site settings service — read and update website configuration.

The SiteSettings table always has exactly one row. This service ensures that
row exists and provides methods to read and update it.
"""

import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site_settings import SiteSettings
from app.schemas.site_settings import SiteSettingsUpdate

logger = logging.getLogger(__name__)


class SiteSettingsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_settings(self) -> SiteSettings:
        """
        Return the single SiteSettings row, creating it with defaults if needed.
        This is safe to call repeatedly — it's idempotent.
        """
        result = await self.db.execute(select(SiteSettings).limit(1))
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = SiteSettings()
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)
            logger.info("SiteSettings row initialised with defaults")
        return settings

    async def update_settings(self, data: SiteSettingsUpdate) -> SiteSettings:
        """
        Update site settings. Only the fields present in the request body
        are updated (PATCH semantics — exclude_unset=True).
        """
        settings = await self.get_settings()
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(settings, field, value)
        await self.db.commit()
        await self.db.refresh(settings)
        logger.info("Site settings updated")
        return settings

    async def update_logo_path(self, path: str) -> SiteSettings:
        settings = await self.get_settings()
        settings.logo_path = path
        await self.db.commit()
        return settings

    async def update_qr_path(self, path: str) -> SiteSettings:
        settings = await self.get_settings()
        settings.upi_qr_path = path
        await self.db.commit()
        return settings
