import { useState, useRef, useEffect } from 'react';
import api from '../services/api';
import './ImageViewer.css';

// ---------------------------------------------------------------------------
// 상수
// ---------------------------------------------------------------------------
const ZOOM_MIN = 0.5;
const ZOOM_MAX = 4;
const ZOOM_STEP = 0.1;
const ROI_PADDING = 0.05;   // ROI 확장 시 여유 비율
const VIEW_MARGIN = 0.05;   // 기본 뷰어 영역 여백 (5%)

// ---------------------------------------------------------------------------
// 좌표 변환 (이미지 ↔ 뷰). translate + scale 만 (회전 없음).
// ---------------------------------------------------------------------------
function imageToView(ix, iy, offset, totalScale) {
  return {
    x: offset.x + ix * totalScale,
    y: offset.y + iy * totalScale,
  };
}

function viewToImage(vx, vy, offset, totalScale) {
  return {
    x: (vx - offset.x) / totalScale,
    y: (vy - offset.y) / totalScale,
  };
}

function denormCoordinate(coord, imgW, imgH) {
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

function normCoordinate(coord, imgW, imgH) {
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

// ---------------------------------------------------------------------------
// 컴포넌트
// ---------------------------------------------------------------------------
/**
 * 이미지 + 좌표 하이라이트 + 줌/팬 뷰어
 * @param {string} imageHash - 이미지 해시 (hash_img)
 * @param {{top,bottom,left,right}|null} coordinate - 정규화 좌표 (0~1, width/height 기준)
 * @param {(coord) => void} [onChangeCoordinate]
 * @param {boolean} [editable=true] - 좌표 편집(ROI 선택) 기능 활성화 여부
 * @param {boolean} [showHelp=true] - 하단 도움말 표시 여부
 * @param {'contain'|'width'} [fit='contain'] - 초기 뷰에서 이미지 맞춤 방식
 * @param {number} [focusMargin] - ROI 기준 뷰 여백 비율(0~0.3 정도). 미지정 시 기본 0.05
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
  const containerRef = useRef(null);
  const imgRef = useRef(null);
  const initializedViewRef = useRef(false);

  const [naturalSize, setNaturalSize] = useState({ width: 0, height: 0 });
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [imageUrl, setImageUrl] = useState('');

  const [dragging, setDragging] = useState(false);
  const [selecting, setSelecting] = useState(false);
  const [selectEnd, setSelectEnd] = useState(null);

  const [modAlt, setModAlt] = useState(false);

  const dragStartRef = useRef({ x: 0, y: 0 });
  const offsetStartRef = useRef({ x: 0, y: 0 });
  const selectStartRef = useRef({ x: 0, y: 0 });

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

  const toView = (x, y) => imageToView(x, y, offset, totalScale);

  // 마지막으로 포커싱에 사용한 픽셀 좌표를 보관하여,
  // 좌표가 실제로 바뀐 경우에만 초기 포커스를 다시 계산한다.
  const lastPixelCoordinateRef = useRef(null);

  // -------------------------------------------------------------------------
  // 효과: 컨테이너 크기
  // -------------------------------------------------------------------------
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const updateSize = () => {
      const rect = el.getBoundingClientRect();
      setContainerSize({ width: rect.width, height: rect.height });
    };
    updateSize();
    const ro = new ResizeObserver(updateSize);
    ro.observe(el);
    window.addEventListener('resize', updateSize);
    return () => {
      ro.disconnect();
      window.removeEventListener('resize', updateSize);
    };
  }, []);

  // -------------------------------------------------------------------------
  // 효과: Alt 키 상태 (커서용)
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!editable) {
      setModAlt(false);
      return;
    }
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

  // -------------------------------------------------------------------------
  // 효과: 이미지 로드
  // -------------------------------------------------------------------------
  useEffect(() => {
    let revokedUrl = null;
    if (!imageHash) {
      setImageUrl('');
      return;
    }
    (async () => {
      try {
        const res = await api.get(`/api/tenant/data-mapping/image/${imageHash}`, { responseType: 'blob' });
        const url = URL.createObjectURL(res.data);
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

  // -------------------------------------------------------------------------
  // 효과: 초기 뷰 (ROI가 신 뷰어 영역에 꽉 차게)
  // -------------------------------------------------------------------------
  useEffect(() => {
    // 좌표가 변경된 경우에는 초기화 플래그를 리셋하여 새 좌표 기준으로 다시 포커싱한다.
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
    const { width: imgW, height: imgH } = naturalSize;
    const { width: viewW, height: viewH } = containerSize;
    if (imgW <= 0 || imgH <= 0 || viewW <= 0 || viewH <= 0 || baseScale <= 0) return;

    const { left: roiLeft, right: roiRight, top: roiTop, bottom: roiBottom } = pixelCoordinate;
    const roiW = Math.max(1, roiRight - roiLeft);
    const roiH = Math.max(1, roiBottom - roiTop);
    const padX = roiW * ROI_PADDING;
    const padY = roiH * ROI_PADDING;

    const extLeft = Math.max(0, roiLeft - padX);
    const extTop = Math.max(0, roiTop - padY);
    const extRight = Math.min(imgW, roiRight + padX);
    const extBottom = Math.min(imgH, roiBottom + padY);
    const extW = Math.max(1, extRight - extLeft);
    const extH = Math.max(1, extBottom - extTop);

    const margin = typeof focusMargin === 'number' ? Math.max(0, Math.min(0.3, focusMargin)) : VIEW_MARGIN;

    const nvLeft = viewW * margin;
    const nvTop = viewH * 0.05; // 상단 5% 지점에 포커스 영역 상단을 맞추기 위함
    const nvW = viewW * (1 - 2 * margin);
    const nvH = viewH * (1 - 2 * margin);

    // 포커스(roi) 자체가 가로 기준으로 (1 - 2*margin) 폭에 맞도록 스케일을 계산한다.
    // extW 는 패딩 포함 확장 영역이므로, 여백 비율을 정확히 맞추려면 roiW 를 기준으로 잡아야 한다.
    const scaleX = nvW / roiW;
    const scaleY = nvH / extH; // 세로는 참고용(현재는 가로를 우선)
    if (!isFinite(scaleX) || scaleX <= 0) return;

    const scale = scaleX;
    if (!isFinite(scale) || scale <= 0) return;
    const newZoom = scale / baseScale;
    const total = baseScale * newZoom;

    setZoom(newZoom);
    setOffset({
      // 포커스 영역(roi)의 왼쪽이 nvLeft(= viewW * margin)에 오도록 정렬
      x: nvLeft - roiLeft * total,
      // 세로는 실제 포커스 상단이 컨테이너 높이의 5% 지점(nvTop)에 오도록 정렬
      y: nvTop - roiTop * total,
    });
    initializedViewRef.current = true;
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

  const handleWheel = (e) => {
    e.preventDefault();
    const dir = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP;
    setZoom((prev) => Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, prev + dir)));
  };

  const handleMouseDown = (e) => {
    e.preventDefault();
    const pos = getEventPos(e);
    if (!pos) return;

    if (e.altKey && editable && onChangeCoordinate) {
      setSelecting(true);
      selectStartRef.current = pos;
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

  // -------------------------------------------------------------------------
  // 파생: ROI 스타일, dim 사각형들, 선택 박스 스타일
  // -------------------------------------------------------------------------
  let roiStyle = null;
  let dimRects = [];
  if (hasPixelCoordinate && totalScale > 0) {
    const { left: l, top: t, right: r, bottom: b } = pixelCoordinate;
    roiStyle = {
      left: `${l}px`,
      top: `${t}px`,
      width: `${r - l}px`,
      height: `${b - t}px`,
    };

    if (containerSize.width > 0 && containerSize.height > 0) {
      const p0 = toView(l, t);
      const p1 = toView(r, t);
      const p2 = toView(r, b);
      const p3 = toView(l, b);
      const minX = Math.min(p0.x, p1.x, p2.x, p3.x);
      const maxX = Math.max(p0.x, p1.x, p2.x, p3.x);
      const minY = Math.min(p0.y, p1.y, p2.y, p3.y);
      const maxY = Math.max(p0.y, p1.y, p2.y, p3.y);
      const top = Math.max(0, minY);
      const left = Math.max(0, minX);
      const right = Math.min(containerSize.width, maxX);
      const bottom = Math.min(containerSize.height, maxY);
      const width = right - left;
      const height = bottom - top;

      if (top > 0) dimRects.push({ top: 0, left: 0, width: containerSize.width, height: top });
      if (bottom < containerSize.height) {
        dimRects.push({ top: bottom, left: 0, width: containerSize.width, height: containerSize.height - bottom });
      }
      if (left > 0 && height > 0) dimRects.push({ top, left: 0, width: left, height });
      if (right < containerSize.width && height > 0) {
        dimRects.push({ top, left: right, width: containerSize.width - right, height });
      }
    }
  }

  let selectStyle = null;
  if (selecting && selectEnd && containerSize.width > 0 && containerSize.height > 0) {
    const start = selectStartRef.current;
    const minX = Math.max(0, Math.min(containerSize.width, Math.min(start.x, selectEnd.x)));
    const maxX = Math.max(0, Math.min(containerSize.width, Math.max(start.x, selectEnd.x)));
    const minY = Math.max(0, Math.min(containerSize.height, Math.min(start.y, selectEnd.y)));
    const maxY = Math.max(0, Math.min(containerSize.height, Math.max(start.y, selectEnd.y)));
    selectStyle = {
      top: `${minY}px`,
      left: `${minX}px`,
      width: `${Math.max(0, maxX - minX)}px`,
      height: `${Math.max(0, maxY - minY)}px`,
    };
  }

  const wrapperTransform = `translate(${offset.x}px, ${offset.y}px) scale(${totalScale})`;
  const isEditMode = selecting;
  const cursorClass = editable && modAlt ? 'image-viewer-cursor-crosshair' : '';

  return (
    <div
      ref={containerRef}
      className={`image-viewer-container ${isEditMode ? 'image-viewer-container-edit' : ''} ${cursorClass}`}
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {imageUrl ? (
        <>
          <div
            className="image-viewer-transform-wrapper"
            style={{ transform: wrapperTransform, transformOrigin: '0 0' }}
          >
            <img
              ref={imgRef}
              src={imageUrl}
              alt="원본 이미지"
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
              Alt+드래그: 영역 재지정 / 드래그: 화면 이동
            </div>
          )}
        </>
      ) : (
        <div className="image-viewer-empty">이미지 경로가 없습니다.</div>
      )}
    </div>
  );
}

export default ImageViewer;
