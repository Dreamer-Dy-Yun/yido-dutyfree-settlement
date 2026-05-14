import { useState, useRef, useEffect } from 'react';
import { KO } from '../locales/KO';
import {
  denormCoordinate,
  getFocusedImageView,
  getRoiOverlay,
  getSelectionStyle,
  normCoordinate,
  viewToImage,
} from './imageViewerGeometry';
import {
  useAltKeyActive,
  useContainerSize,
  useImageBlobUrl,
  useWheelZoom,
} from './useImageViewerResources';
import './ImageViewer.css';

/**
 * 이미지와 ROI 좌표를 함께 표시하는 뷰어.
 * Alt+드래그로 ROI를 재지정하고, 일반 드래그로 화면을 이동한다.
 */
function ImageViewer({
  imageHash,
  coordinate,
  onChangeCoordinate,
  editable = true,
  showHelp = true,
  fit = 'contain',
  focusMargin,
}) {
  const text = KO.dataMapping.imageViewer;

  const containerRef = useRef(null);
  const imgRef = useRef(null);
  const initializedViewRef = useRef(false);

  const [naturalSize, setNaturalSize] = useState({ width: 0, height: 0 });
  const containerSize = useContainerSize(containerRef);
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const imageUrl = useImageBlobUrl(imageHash);

  const [dragging, setDragging] = useState(false);
  const [selecting, setSelecting] = useState(false);
  const [selectStart, setSelectStart] = useState(null);
  const [selectEnd, setSelectEnd] = useState(null);

  const modAlt = useAltKeyActive(editable);

  const dragStartRef = useRef({ x: 0, y: 0 });
  const offsetStartRef = useRef({ x: 0, y: 0 });
  const selectStartRef = useRef({ x: 0, y: 0 });
  useWheelZoom(containerRef, setZoom);

  const hasCoordinate =
    coordinate &&
    typeof coordinate.top === 'number' &&
    typeof coordinate.bottom === 'number' &&
    typeof coordinate.left === 'number' &&
    typeof coordinate.right === 'number';

  const pixelCoordinate =
    hasCoordinate && naturalSize.width > 0 && naturalSize.height > 0
      ? denormCoordinate(coordinate, naturalSize.width, naturalSize.height)
      : null;
  const hasPixelCoordinate =
    pixelCoordinate &&
    typeof pixelCoordinate.top === 'number' &&
    typeof pixelCoordinate.bottom === 'number' &&
    typeof pixelCoordinate.left === 'number' &&
    typeof pixelCoordinate.right === 'number';

  const baseScale =
    naturalSize.width > 0 && naturalSize.height > 0 && containerSize.width > 0 && containerSize.height > 0
      ? fit === 'width'
        ? containerSize.width / naturalSize.width
        : Math.min(containerSize.width / naturalSize.width, containerSize.height / naturalSize.height)
      : 1;
  const totalScale = baseScale * zoom;

  // 마지막 자동 포커스 기준 좌표를 보관해서 실제 좌표 변경 때만 초기 포커스를 재계산한다.
  const lastPixelCoordinateRef = useRef(null);

  useEffect(() => {
    if (hasPixelCoordinate && pixelCoordinate) {
      const last = lastPixelCoordinateRef.current;
      const curr = pixelCoordinate;
      const changed =
        !last ||
        last.top !== curr.top ||
        last.bottom !== curr.bottom ||
        last.left !== curr.left ||
        last.right !== curr.right;
      if (changed) {
        initializedViewRef.current = false;
        lastPixelCoordinateRef.current = { ...curr };
      }
    }

    if (!hasPixelCoordinate || initializedViewRef.current) return;
    const focusedView = getFocusedImageView({
      pixelCoordinate,
      naturalSize,
      containerSize,
      baseScale,
      focusMargin,
    });
    if (!focusedView) return;

    const frameId = requestAnimationFrame(() => {
      setZoom(focusedView.zoom);
      setOffset(focusedView.offset);
      initializedViewRef.current = true;
    });
    return () => cancelAnimationFrame(frameId);
  }, [hasPixelCoordinate, pixelCoordinate, naturalSize, containerSize, baseScale, focusMargin]);

  const getEventPos = (e) => {
    if (!containerRef.current) return null;
    const rect = containerRef.current.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  const handleImageLoad = () => {
    if (!imgRef.current) return;
    setNaturalSize({ width: imgRef.current.naturalWidth, height: imgRef.current.naturalHeight });
    setZoom(1);
    setOffset({ x: 0, y: 0 });
    initializedViewRef.current = false;
  };

  const handleMouseDown = (e) => {
    e.preventDefault();
    const pos = getEventPos(e);
    if (!pos) return;

    if (e.altKey && editable && onChangeCoordinate) {
      setSelecting(true);
      selectStartRef.current = pos;
      setSelectStart(pos);
      setSelectEnd(pos);
    } else if (!e.altKey && !e.ctrlKey) {
      setDragging(true);
      dragStartRef.current = { x: e.clientX, y: e.clientY };
      offsetStartRef.current = { ...offset };
    } else {
      setDragging(false);
      setSelecting(false);
      setSelectEnd(null);
    }
  };

  const handleMouseMove = (e) => {
    if (selecting) {
      e.preventDefault();
      const pos = getEventPos(e);
      if (pos) setSelectEnd(pos);
      return;
    }
    if (!dragging) return;
    e.preventDefault();
    setOffset({
      x: offsetStartRef.current.x + (e.clientX - dragStartRef.current.x),
      y: offsetStartRef.current.y + (e.clientY - dragStartRef.current.y),
    });
  };

  const clearInteractionState = () => {
    setSelecting(false);
    setSelectStart(null);
    setSelectEnd(null);
    setDragging(false);
  };

  const handleMouseUp = () => {
    if (selecting && selectEnd && editable && onChangeCoordinate && naturalSize.width > 0 && naturalSize.height > 0 && totalScale > 0) {
      const start = selectStartRef.current;
      const vMinX = Math.min(start.x, selectEnd.x);
      const vMaxX = Math.max(start.x, selectEnd.x);
      const vMinY = Math.min(start.y, selectEnd.y);
      const vMaxY = Math.max(start.y, selectEnd.y);

      const topLeft = viewToImage(vMinX, vMinY, offset, totalScale);
      const bottomRight = viewToImage(vMaxX, vMaxY, offset, totalScale);
      const leftPx = Math.min(topLeft.x, bottomRight.x);
      const rightPx = Math.max(topLeft.x, bottomRight.x);
      const topPx = Math.min(topLeft.y, bottomRight.y);
      const bottomPx = Math.max(topLeft.y, bottomRight.y);

      const left = Math.max(0, Math.min(naturalSize.width, leftPx));
      const right = Math.max(0, Math.min(naturalSize.width, rightPx));
      const top = Math.max(0, Math.min(naturalSize.height, topPx));
      const bottom = Math.max(0, Math.min(naturalSize.height, bottomPx));

      if (onChangeCoordinate && right - left > 1 && bottom - top > 1) {
        const norm = normCoordinate(
          { top, bottom, left, right },
          naturalSize.width,
          naturalSize.height,
        );
        if (norm) {
          onChangeCoordinate(norm);
        }
      }
    }

    clearInteractionState();
  };

  const { roiStyle, dimRects } = getRoiOverlay({
    pixelCoordinate: hasPixelCoordinate ? pixelCoordinate : null,
    containerSize,
    offset,
    totalScale,
  });
  const selectStyle = getSelectionStyle({ selecting, selectStart, selectEnd, containerSize });

  const wrapperTransform = `translate(${offset.x}px, ${offset.y}px) scale(${totalScale})`;
  const isEditMode = selecting;
  const cursorClass = editable && modAlt ? 'image-viewer-cursor-crosshair' : '';
  const currentImageUrl = imageHash ? imageUrl : '';

  return (
    <div
      ref={containerRef}
      className={`image-viewer-container ${isEditMode ? 'image-viewer-container-edit' : ''} ${cursorClass}`}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {currentImageUrl ? (
        <>
          <div
            className="image-viewer-transform-wrapper"
            style={{ transform: wrapperTransform, transformOrigin: '0 0' }}
          >
            <img
              ref={imgRef}
              src={currentImageUrl}
              alt={text.altText}
              className="image-viewer-image"
              onLoad={handleImageLoad}
              draggable={false}
            />
            {roiStyle && (
              <div className="image-viewer-roi" style={roiStyle}>
                <div className="image-viewer-roi-inner" />
              </div>
            )}
          </div>
          {dimRects.map((rect, idx) => (
            <div
              key={idx}
              className="image-viewer-dim"
              style={{
                top: `${rect.top}px`,
                left: `${rect.left}px`,
                width: `${rect.width}px`,
                height: `${rect.height}px`,
              }}
            />
          ))}
          {selectStyle && <div className="image-viewer-selection" style={selectStyle} />}
          {editable && showHelp && (
            <div className="image-viewer-help">
              {text.help}
            </div>
          )}
        </>
      ) : (
        <div className="image-viewer-empty">{text.empty}</div>
      )}
    </div>
  );
}

export default ImageViewer;
