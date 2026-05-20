import { useEffect, useState } from 'react';
import { getImageBlobByHash } from '../api/data-mapping/imageAssetApi';
import { ZOOM_MIN, ZOOM_MAX, ZOOM_STEP } from './imageViewerGeometry';

export function useContainerSize(containerRef) {
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return undefined;

    const updateSize = () => {
      const rect = el.getBoundingClientRect();
      setContainerSize({ width: rect.width, height: rect.height });
    };
    updateSize();

    const resizeObserver = new ResizeObserver(updateSize);
    resizeObserver.observe(el);
    window.addEventListener('resize', updateSize);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', updateSize);
    };
  }, [containerRef]);

  return containerSize;
}

export function useAltKeyActive(editable) {
  const [modAlt, setModAlt] = useState(false);

  useEffect(() => {
    if (!editable) return undefined;

    const onKeyDown = (e) => {
      if (e.key === 'Alt') setModAlt(true);
    };
    const onKeyUp = (e) => {
      if (e.key === 'Alt') setModAlt(false);
    };
    const onBlur = () => setModAlt(false);

    window.addEventListener('keydown', onKeyDown, true);
    window.addEventListener('keyup', onKeyUp, true);
    window.addEventListener('blur', onBlur);

    return () => {
      window.removeEventListener('keydown', onKeyDown, true);
      window.removeEventListener('keyup', onKeyUp, true);
      window.removeEventListener('blur', onBlur);
    };
  }, [editable]);

  return modAlt;
}

export function useImageBlobUrl(imageHash) {
  const [imageUrl, setImageUrl] = useState('');

  useEffect(() => {
    let revokedUrl = null;
    if (!imageHash) return undefined;

    (async () => {
      try {
        const blob = await getImageBlobByHash(imageHash);
        const url = URL.createObjectURL(blob);
        revokedUrl = url;
        setImageUrl(url);
      } catch {
        setImageUrl('');
      }
    })();

    return () => {
      if (revokedUrl) URL.revokeObjectURL(revokedUrl);
    };
  }, [imageHash]);

  return imageHash ? imageUrl : '';
}

export function useWheelZoom(containerRef, setZoom) {
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return undefined;

    const onWheel = (e) => {
      e.preventDefault();
      const dir = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP;
      setZoom((prev) => Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, prev + dir)));
    };

    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, [containerRef, setZoom]);
}
