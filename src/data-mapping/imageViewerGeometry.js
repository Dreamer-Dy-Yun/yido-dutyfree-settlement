export const ZOOM_MIN = 0.5;
export const ZOOM_MAX = 4;
export const ZOOM_STEP = 0.1;
export const VIEW_MARGIN = 0.05;

export function imageToView(ix, iy, offset, totalScale) {
  return {
    x: offset.x + ix * totalScale,
    y: offset.y + iy * totalScale,
  };
}

export function viewToImage(vx, vy, offset, totalScale) {
  return {
    x: (vx - offset.x) / totalScale,
    y: (vy - offset.y) / totalScale,
  };
}

export function denormCoordinate(coord, imgW, imgH) {
  if (
    !coord ||
    typeof imgW !== 'number' ||
    typeof imgH !== 'number' ||
    imgW <= 0 ||
    imgH <= 0
  ) {
    return null;
  }
  return {
    top: coord.top * imgH,
    bottom: coord.bottom * imgH,
    left: coord.left * imgW,
    right: coord.right * imgW,
  };
}

export function normCoordinate(coord, imgW, imgH) {
  if (
    !coord ||
    typeof imgW !== 'number' ||
    typeof imgH !== 'number' ||
    imgW <= 0 ||
    imgH <= 0
  ) {
    return null;
  }
  return {
    top: coord.top / imgH,
    bottom: coord.bottom / imgH,
    left: coord.left / imgW,
    right: coord.right / imgW,
  };
}

export function getFocusedImageView({
  pixelCoordinate,
  naturalSize,
  containerSize,
  baseScale,
  focusMargin,
}) {
  const { width: imgW, height: imgH } = naturalSize;
  const { width: viewW, height: viewH } = containerSize;
  if (!pixelCoordinate || imgW <= 0 || imgH <= 0 || viewW <= 0 || viewH <= 0 || baseScale <= 0) {
    return null;
  }

  const { left: roiLeft, right: roiRight, top: roiTop } = pixelCoordinate;
  const roiW = Math.max(1, roiRight - roiLeft);
  const margin = typeof focusMargin === 'number'
    ? Math.max(0, Math.min(0.3, focusMargin))
    : VIEW_MARGIN;

  const viewLeft = viewW * margin;
  const viewTop = viewH * 0.05;
  const viewWidth = viewW * (1 - 2 * margin);
  const scale = viewWidth / roiW;
  if (!Number.isFinite(scale) || scale <= 0) return null;

  const zoom = scale / baseScale;
  const totalScale = baseScale * zoom;
  return {
    zoom,
    offset: {
      x: viewLeft - roiLeft * totalScale,
      y: viewTop - roiTop * totalScale,
    },
  };
}

export function getRoiOverlay({ pixelCoordinate, containerSize, offset, totalScale }) {
  if (!pixelCoordinate || totalScale <= 0) {
    return { roiStyle: null, dimRects: [] };
  }

  const { left, top, right, bottom } = pixelCoordinate;
  const roiStyle = {
    left: `${left}px`,
    top: `${top}px`,
    width: `${right - left}px`,
    height: `${bottom - top}px`,
  };
  const dimRects = [];

  if (containerSize.width <= 0 || containerSize.height <= 0) {
    return { roiStyle, dimRects };
  }

  const p0 = imageToView(left, top, offset, totalScale);
  const p1 = imageToView(right, top, offset, totalScale);
  const p2 = imageToView(right, bottom, offset, totalScale);
  const p3 = imageToView(left, bottom, offset, totalScale);
  const minX = Math.min(p0.x, p1.x, p2.x, p3.x);
  const maxX = Math.max(p0.x, p1.x, p2.x, p3.x);
  const minY = Math.min(p0.y, p1.y, p2.y, p3.y);
  const maxY = Math.max(p0.y, p1.y, p2.y, p3.y);
  const clampedTop = Math.max(0, minY);
  const clampedLeft = Math.max(0, minX);
  const clampedRight = Math.min(containerSize.width, maxX);
  const clampedBottom = Math.min(containerSize.height, maxY);
  const height = clampedBottom - clampedTop;

  if (clampedTop > 0) {
    dimRects.push({ top: 0, left: 0, width: containerSize.width, height: clampedTop });
  }
  if (clampedBottom < containerSize.height) {
    dimRects.push({
      top: clampedBottom,
      left: 0,
      width: containerSize.width,
      height: containerSize.height - clampedBottom,
    });
  }
  if (clampedLeft > 0 && height > 0) {
    dimRects.push({ top: clampedTop, left: 0, width: clampedLeft, height });
  }
  if (clampedRight < containerSize.width && height > 0) {
    dimRects.push({
      top: clampedTop,
      left: clampedRight,
      width: containerSize.width - clampedRight,
      height,
    });
  }

  return { roiStyle, dimRects };
}

export function getSelectionStyle({ selecting, selectStart, selectEnd, containerSize }) {
  if (!selecting || !selectStart || !selectEnd || containerSize.width <= 0 || containerSize.height <= 0) {
    return null;
  }

  const minX = Math.max(0, Math.min(containerSize.width, Math.min(selectStart.x, selectEnd.x)));
  const maxX = Math.max(0, Math.min(containerSize.width, Math.max(selectStart.x, selectEnd.x)));
  const minY = Math.max(0, Math.min(containerSize.height, Math.min(selectStart.y, selectEnd.y)));
  const maxY = Math.max(0, Math.min(containerSize.height, Math.max(selectStart.y, selectEnd.y)));

  return {
    top: `${minY}px`,
    left: `${minX}px`,
    width: `${Math.max(0, maxX - minX)}px`,
    height: `${Math.max(0, maxY - minY)}px`,
  };
}
