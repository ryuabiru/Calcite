import { forwardRef } from "react";

const WIDTH = 920;
const HEIGHT = 380;
const SVG_FONT_FAMILY = "Aptos, Segoe UI, Helvetica Neue, sans-serif";
const MARGIN = {
  top: 34,
  right: 26,
  bottom: 52,
  left: 64,
};

const SERIES_COLORS = ["#3f6f8f", "#4b7d7a", "#8a6fb1", "#b07c45", "#6d7f98", "#b55c68"];

function isFiniteNumber(value) {
  return Number.isFinite(value) && !Number.isNaN(value);
}

function parseNumber(value) {
  const parsed = Number.parseFloat(String(value).trim());
  return Number.isFinite(parsed) ? parsed : null;
}

function formatNumber(value) {
  if (!Number.isFinite(value)) {
    return "";
  }
  if (Math.abs(value - Math.round(value)) < 1e-9) {
    return `${Math.round(value)}`;
  }
  return value.toFixed(2);
}

function getPlotArea() {
  return {
    left: MARGIN.left,
    right: WIDTH - MARGIN.right,
    top: MARGIN.top,
    bottom: HEIGHT - MARGIN.bottom,
    width: WIDTH - MARGIN.left - MARGIN.right,
    height: HEIGHT - MARGIN.top - MARGIN.bottom,
  };
}

function buildCategoricalLayout(categoryCount, options = {}) {
  const plot = getPlotArea();
  const safeCount = Math.max(categoryCount, 1);
  const gapRatio = options.gapRatio ?? 0.28;
  const outerPadding = options.outerPadding ?? 0.18;
  const totalStep = plot.width / safeCount;
  const bandWidth = totalStep * (1 - gapRatio);
  const innerWidth = bandWidth * (1 - outerPadding * 2);
  const xScale = (index) => plot.left + totalStep * index + totalStep / 2;
  return {
    plot,
    xScale,
    totalStep,
    bandWidth,
    innerWidth: Math.max(12, innerWidth),
  };
}

function getVisibleRows(snapshot) {
  const indices =
    snapshot.visible_row_indices.length > 0 || snapshot.row_filter_query.trim() !== ""
      ? snapshot.visible_row_indices
      : snapshot.rows.map((_, index) => index);
  return indices.map((rowIndex) => snapshot.rows[rowIndex]).filter((row) => Array.isArray(row));
}

function getColumnIndex(snapshot, name) {
  return snapshot.headers.findIndex((header) => header === name);
}

function collectSeriesRows(rows, snapshot, xName, yName, subgroupName) {
  const xIndex = getColumnIndex(snapshot, xName);
  const yIndex = getColumnIndex(snapshot, yName);
  const subgroupIndex = subgroupName ? getColumnIndex(snapshot, subgroupName) : -1;
  if (xIndex < 0 || yIndex < 0) {
    return null;
  }

  const seriesMap = new Map();
  const categories = [];
  const numericXValues = [];
  const numericYValues = [];

  for (const row of rows) {
    const rawX = row[xIndex] ?? "";
    const rawY = row[yIndex] ?? "";
    const yValue = parseNumber(rawY);
    if (yValue === null) {
      continue;
    }

    const subgroupLabel =
      subgroupIndex >= 0 ? String(row[subgroupIndex] ?? "").trim() || "(empty)" : "All";
    const categoryLabel = String(rawX ?? "").trim() || "(empty)";
    const xValue = parseNumber(rawX);

    if (!seriesMap.has(subgroupLabel)) {
      seriesMap.set(subgroupLabel, []);
    }
    seriesMap.get(subgroupLabel).push({
      xValue,
      categoryLabel,
      yValue,
      rawX: String(rawX ?? ""),
      rawY: String(rawY ?? ""),
    });
    if (!categories.includes(categoryLabel)) {
      categories.push(categoryLabel);
    }
    if (xValue !== null) {
      numericXValues.push(xValue);
    }
    numericYValues.push(yValue);
  }

  if (seriesMap.size === 0) {
    return null;
  }

  return {
    seriesMap,
    categories,
    numericXValues,
    numericYValues,
    xName,
    yName,
    subgroupName,
  };
}

function summarizeCategorySeries(seriesMap, categories) {
  const summary = new Map();

  for (const [seriesLabel, rows] of seriesMap.entries()) {
    const categoryMap = new Map();
    for (const row of rows) {
      if (!categoryMap.has(row.categoryLabel)) {
        categoryMap.set(row.categoryLabel, []);
      }
      categoryMap.get(row.categoryLabel).push(row.yValue);
    }

    summary.set(
      seriesLabel,
      categories.map((category) => {
        const values = categoryMap.get(category) || [];
        if (values.length === 0) {
          return { category, count: 0, mean: null, min: null, max: null, values: [] };
        }
        const sorted = [...values].sort((a, b) => a - b);
        const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
        const min = sorted[0];
        const max = sorted[sorted.length - 1];
        return { category, count: values.length, mean, min, max, values: sorted };
      }),
    );
  }

  return summary;
}

function summarizeNumericSeries(seriesMap) {
  const summary = new Map();
  for (const [seriesLabel, rows] of seriesMap.entries()) {
    const values = rows
      .map((row) => row.yValue)
      .filter((value) => Number.isFinite(value))
      .sort((a, b) => a - b);
    if (values.length === 0) {
      summary.set(seriesLabel, []);
      continue;
    }
    summary.set(seriesLabel, values);
  }
  return summary;
}

function summarizeCategoricalCounts(rows, snapshot, xName, subgroupName) {
  const xIndex = getColumnIndex(snapshot, xName);
  const subgroupIndex = subgroupName ? getColumnIndex(snapshot, subgroupName) : -1;
  if (xIndex < 0) {
    return null;
  }

  const categories = [];
  const seriesMap = new Map();

  for (const row of rows) {
    const category = String(row[xIndex] ?? "").trim() || "(empty)";
    const subgroupLabel =
      subgroupIndex >= 0 ? String(row[subgroupIndex] ?? "").trim() || "(empty)" : "All";
    if (!categories.includes(category)) {
      categories.push(category);
    }
    if (!seriesMap.has(subgroupLabel)) {
      seriesMap.set(subgroupLabel, new Map());
    }
    const categoryMap = seriesMap.get(subgroupLabel);
    categoryMap.set(category, (categoryMap.get(category) || 0) + 1);
  }

  return { categories, seriesMap };
}

function pearsonCorrelation(valuesX, valuesY) {
  const pairs = valuesX
    .map((x, index) => [x, valuesY[index]])
    .filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y));
  if (pairs.length < 2) {
    return null;
  }
  const meanX = pairs.reduce((sum, [x]) => sum + x, 0) / pairs.length;
  const meanY = pairs.reduce((sum, [, y]) => sum + y, 0) / pairs.length;
  let numerator = 0;
  let sumSqX = 0;
  let sumSqY = 0;
  for (const [x, y] of pairs) {
    const dx = x - meanX;
    const dy = y - meanY;
    numerator += dx * dy;
    sumSqX += dx * dx;
    sumSqY += dy * dy;
  }
  const denominator = Math.sqrt(sumSqX * sumSqY);
  if (denominator <= 1e-9) {
    return null;
  }
  return numerator / denominator;
}

function collectNumericColumns(snapshot, rows) {
  return snapshot.headers
    .map((header, columnIndex) => {
      const values = rows
        .map((row) => parseNumber(row[columnIndex]))
        .filter((value) => Number.isFinite(value));
      return { header, columnIndex, values };
    })
    .filter((column) => column.values.length > 0);
}

function drawBarPlot({ snapshot, rows, xName, yName, subgroupName, annotationSummary }) {
  const cloud = collectSeriesRows(rows, snapshot, xName, yName, subgroupName);
  if (!cloud) {
    return renderNoData("No bar data", "Choose a categorical X column and numeric Y column.");
  }
  const summary = summarizeCategorySeries(cloud.seriesMap, cloud.categories);
  const groups = [...summary.entries()];
  if (groups.length === 0) {
    return renderNoData("No bar data", "No values were available.");
  }

  const allMeans = groups.flatMap(([, values]) => values.map((entry) => entry.mean).filter(Number.isFinite));
  const yDomain = { min: 0, max: Math.max(...allMeans, 1) * 1.15 };
  const layout = buildCategoricalLayout(cloud.categories.length, { gapRatio: 0.24, outerPadding: 0.12 });
  const xScale = layout.xScale;
  const yScale = buildLinearScale(yDomain.min, yDomain.max, HEIGHT - MARGIN.bottom, MARGIN.top);
  const seriesCount = groups.length;
  const barWidth = Math.max(10, layout.innerWidth / Math.max(seriesCount, 1) - 4);
  const annotations = parseAnnotationSummary(annotationSummary);

  return (
    <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} fontFamily={SVG_FONT_FAMILY}>
      <rect x="0" y="0" width={WIDTH} height={HEIGHT} rx="18" fill="#fffaf3" stroke="#e0ccb4" />
      {axisLabel({ xName, yName, subtitle: snapshot.current_graph_type })}
      {renderHorizontalGridLines()}
      {renderYAxisTickLabels({ domainMin: yDomain.min, domainMax: yDomain.max })}
      {renderVerticalGridLines(Math.max(cloud.categories.length, 4))}
      {renderTopRightSpines()}
      {cloud.categories.map((category, index) => (
        <text
          key={`bar-x-${category}`}
          x={xScale(index)}
          y={HEIGHT - 24}
          textAnchor="middle"
          fontSize="12"
          fill="#6b5d4d"
        >
          {category}
        </text>
      ))}
      {[...groups].map(([seriesLabel, values], seriesIndex) => {
        const color = SERIES_COLORS[seriesIndex % SERIES_COLORS.length];
        return (
          <g key={seriesLabel}>
            {values.map((entry, categoryIndex) => {
              if (!Number.isFinite(entry.mean)) {
                return null;
              }
              const slotWidth = layout.innerWidth / Math.max(seriesCount, 1);
              const xCenter =
                xScale(categoryIndex) +
                (seriesIndex - (seriesCount - 1) / 2) * slotWidth;
              const barTop = yScale(entry.mean);
              return (
                <g key={`${seriesLabel}-${entry.category}`}>
                  <title>{`${seriesLabel} / ${entry.category}: ${formatNumber(entry.mean)}`}</title>
                  <rect
                    x={xCenter - barWidth / 2}
                    y={barTop}
                    width={barWidth}
                    height={HEIGHT - MARGIN.bottom - barTop}
                    fill={color}
                    opacity="0.82"
                  />
                </g>
              );
            })}
          </g>
        );
      })}
      {renderPrimaryAxes()}
      {renderPairAnnotations({
        annotations,
        categories: cloud.categories,
        xScale,
        baseY: MARGIN.top + 26,
      })}
    </svg>
  );
}

function drawCountPlot({ snapshot, rows, xName, subgroupName, annotationSummary }) {
  const summary = summarizeCategoricalCounts(rows, snapshot, xName, subgroupName);
  if (!summary) {
    return renderNoData("No count plot data", "Choose a categorical X column.");
  }
  const maxCount = Math.max(
    1,
    ...[...summary.seriesMap.values()].flatMap((categoryMap) => [...categoryMap.values()]),
  );
  const layout = buildCategoricalLayout(summary.categories.length, { gapRatio: 0.24, outerPadding: 0.12 });
  const xScale = layout.xScale;
  const yScale = buildLinearScale(0, maxCount * 1.2, HEIGHT - MARGIN.bottom, MARGIN.top);
  const groups = [...summary.seriesMap.entries()];
  const barWidth = Math.max(10, layout.innerWidth / Math.max(groups.length, 1) - 4);
  const annotations = parseAnnotationSummary(annotationSummary);

  return (
    <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} fontFamily={SVG_FONT_FAMILY}>
      <rect x="0" y="0" width={WIDTH} height={HEIGHT} rx="18" fill="#fffaf3" stroke="#e0ccb4" />
      {axisLabel({ xName, yName: "Count", subtitle: snapshot.current_graph_type })}
      {renderHorizontalGridLines()}
      {renderYAxisTickLabels({ domainMin: 0, domainMax: maxCount * 1.2 })}
      {renderVerticalGridLines(Math.max(summary.categories.length, 4))}
      {renderTopRightSpines()}
      {summary.categories.map((category, index) => (
        <text key={`count-x-${category}`} x={xScale(index)} y={HEIGHT - 24} textAnchor="middle" fontSize="12" fill="#6b5d4d">
          {category}
        </text>
      ))}
      {groups.map(([seriesLabel, categoryMap], seriesIndex) => {
        const color = SERIES_COLORS[seriesIndex % SERIES_COLORS.length];
        return (
          <g key={seriesLabel}>
            {summary.categories.map((category, categoryIndex) => {
              const count = categoryMap.get(category) || 0;
              const slotWidth = layout.innerWidth / Math.max(groups.length, 1);
              const xCenter =
                xScale(categoryIndex) +
                (seriesIndex - (groups.length - 1) / 2) * slotWidth;
              const barTop = yScale(count);
              return (
                <g key={`${seriesLabel}-${category}`}>
                  <title>{`${seriesLabel} / ${category}: ${count}`}</title>
                  <rect
                    x={xCenter - barWidth / 2}
                    y={barTop}
                    width={barWidth}
                    height={HEIGHT - MARGIN.bottom - barTop}
                    fill={color}
                    opacity="0.8"
                  />
                </g>
              );
            })}
          </g>
        );
      })}
      {renderPrimaryAxes()}
      {renderPairAnnotations({
        annotations,
        categories: summary.categories,
        xScale,
        baseY: MARGIN.top + 26,
      })}
    </svg>
  );
}

function drawStackedBarPlot({ snapshot, rows, xName, subgroupName, normalized = false, annotationSummary }) {
  const summary = summarizeCategoricalCounts(rows, snapshot, xName, subgroupName);
  if (!summary) {
    return renderNoData("No stacked bar data", "Choose a categorical X column.");
  }
  const groups = [...summary.seriesMap.entries()];
  if (groups.length === 0) {
    return renderNoData("No stacked bar data", "No values were available.");
  }

  const layout = buildCategoricalLayout(summary.categories.length, { gapRatio: 0.3, outerPadding: 0.08 });
  const xScale = layout.xScale;
  const bandWidth = Math.max(18, layout.innerWidth);
  const yMax = normalized ? 1 : Math.max(
    1,
    ...summary.categories.map((category) =>
      groups.reduce((sum, [, categoryMap]) => sum + (categoryMap.get(category) || 0), 0),
    ),
  );
  const yScale = buildLinearScale(0, yMax * 1.1, HEIGHT - MARGIN.bottom, MARGIN.top);
  const annotations = parseAnnotationSummary(annotationSummary);

  return (
    <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} fontFamily={SVG_FONT_FAMILY}>
      <rect x="0" y="0" width={WIDTH} height={HEIGHT} rx="18" fill="#fffaf3" stroke="#e0ccb4" />
      {axisLabel({ xName, yName: normalized ? "Proportion" : "Count", subtitle: snapshot.current_graph_type })}
      {renderHorizontalGridLines()}
      {renderYAxisTickLabels({
        domainMin: 0,
        domainMax: yMax * 1.1,
        formatter: normalized ? (value) => `${Math.round(value * 100)}%` : formatNumber,
      })}
      {renderVerticalGridLines(Math.max(summary.categories.length, 4))}
      {renderTopRightSpines()}
      {summary.categories.map((category, index) => (
        <text key={`stack-x-${category}`} x={xScale(index)} y={HEIGHT - 24} textAnchor="middle" fontSize="12" fill="#6b5d4d">
          {category}
        </text>
      ))}
      {summary.categories.map((category, categoryIndex) => {
        let offset = 0;
        const total = groups.reduce((sum, [, categoryMap]) => sum + (categoryMap.get(category) || 0), 0);
        return (
          <g key={category}>
            <title>{`${category}: ${normalized ? `${formatNumber(total)} total` : `${formatNumber(total)} count`}`}</title>
            {groups.map(([seriesLabel, categoryMap], seriesIndex) => {
              const rawCount = categoryMap.get(category) || 0;
              if (rawCount === 0) {
                return null;
              }
              const value = normalized ? rawCount / Math.max(total, 1) : rawCount;
              const nextOffset = offset + value;
              const yTop = yScale(nextOffset);
              const yBottom = yScale(offset);
              const color = SERIES_COLORS[seriesIndex % SERIES_COLORS.length];
              const barX = xScale(categoryIndex) - bandWidth / 2;
              offset = nextOffset;
              return (
                <rect
                  key={`${category}-${seriesLabel}`}
                  x={barX}
                  y={yTop}
                  width={bandWidth}
                  height={Math.max(1, yBottom - yTop)}
                  fill={color}
                  opacity="0.82"
                />
              );
            })}
          </g>
        );
      })}
      {renderPrimaryAxes()}
      {renderPairAnnotations({
        annotations,
        categories: summary.categories,
        xScale,
        baseY: MARGIN.top + 26,
      })}
    </svg>
  );
}

function drawHistogram({ snapshot, rows, xName }) {
  const xIndex = getColumnIndex(snapshot, xName);
  if (xIndex < 0) {
    return renderNoData("No histogram data", "Choose a numeric X column.");
  }
  const values = rows.map((row) => parseNumber(row[xIndex])).filter((value) => Number.isFinite(value));
  if (values.length === 0) {
    return renderNoData("No histogram data", "No numeric values were found.");
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const bins = Math.min(12, Math.max(5, Math.ceil(Math.sqrt(values.length))));
  const span = Math.max(max - min, 1e-9);
  const counts = Array.from({ length: bins }, () => 0);
  values.forEach((value) => {
    let index = Math.floor(((value - min) / span) * bins);
    if (index >= bins) index = bins - 1;
    if (index < 0) index = 0;
    counts[index] += 1;
  });
  const maxCount = Math.max(...counts, 1);
  const layout = buildCategoricalLayout(bins, { gapRatio: 0.24, outerPadding: 0.1 });
  const xScale = layout.xScale;
  const yScale = buildLinearScale(0, maxCount * 1.2, HEIGHT - MARGIN.bottom, MARGIN.top);
  const barWidth = Math.max(12, layout.innerWidth);

  return (
    <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} fontFamily={SVG_FONT_FAMILY}>
      <rect x="0" y="0" width={WIDTH} height={HEIGHT} rx="18" fill="#fffaf3" stroke="#e0ccb4" />
      {axisLabel({ xName, yName: "Count", subtitle: snapshot.current_graph_type })}
      {renderHorizontalGridLines()}
      {renderYAxisTickLabels({ domainMin: 0, domainMax: maxCount * 1.2 })}
      {renderVerticalGridLines(Math.max(bins, 4))}
      {renderTopRightSpines()}
      {counts.map((count, index) => {
        const x = xScale(index);
        const barTop = yScale(count);
        return (
          <g key={`hist-${index}`}>
            <title>{`${formatNumber(min + (index / bins) * span)} - ${formatNumber(min + ((index + 1) / bins) * span)}: ${count}`}</title>
            <rect
              x={x - barWidth / 2}
              y={barTop}
              width={barWidth}
              height={HEIGHT - MARGIN.bottom - barTop}
              fill="#b65d22"
              opacity="0.82"
            />
            <text x={x} y={HEIGHT - 24} textAnchor="middle" fontSize="11" fill="#6b5d4d">
              {formatNumber(min + (index / bins) * span)}
            </text>
          </g>
        );
      })}
      {renderPrimaryAxes()}
    </svg>
  );
}

function drawHeatmap({ snapshot, rows, xName, yName }) {
  const xIndex = getColumnIndex(snapshot, xName);
  const yIndex = getColumnIndex(snapshot, yName);
  if (xIndex < 0 || yIndex < 0) {
    return renderNoData("No heatmap data", "Choose X and Y columns.");
  }
  const table = new Map();
  const xCategories = [];
  const yCategories = [];
  for (const row of rows) {
    const xLabel = String(row[xIndex] ?? "").trim() || "(empty)";
    const yLabel = String(row[yIndex] ?? "").trim() || "(empty)";
    if (!xCategories.includes(xLabel)) xCategories.push(xLabel);
    if (!yCategories.includes(yLabel)) yCategories.push(yLabel);
    const key = `${xLabel}::${yLabel}`;
    table.set(key, (table.get(key) || 0) + 1);
  }
  if (xCategories.length === 0 || yCategories.length === 0) {
    return renderNoData("No heatmap data", "No categorical values were found.");
  }
  const maxCount = Math.max(1, ...table.values());
  const cellWidth = (WIDTH - MARGIN.left - MARGIN.right) / Math.max(xCategories.length, 1);
  const cellHeight = (HEIGHT - MARGIN.top - MARGIN.bottom) / Math.max(yCategories.length, 1);

  return (
    <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} fontFamily={SVG_FONT_FAMILY}>
      <rect x="0" y="0" width={WIDTH} height={HEIGHT} rx="18" fill="#fffaf3" stroke="#e0ccb4" />
      {axisLabel({ xName, yName, subtitle: snapshot.current_graph_type })}
      {renderHorizontalGridLines()}
      {renderVerticalGridLines(Math.max(xCategories.length, 4))}
      <line x1={MARGIN.left} y1={HEIGHT - MARGIN.bottom} x2={WIDTH - MARGIN.right} y2={HEIGHT - MARGIN.bottom} stroke="#6b5d4d" />
      <line x1={MARGIN.left} y1={MARGIN.top} x2={MARGIN.left} y2={HEIGHT - MARGIN.bottom} stroke="#6b5d4d" />
      {xCategories.map((label, index) => (
        <text key={`hm-x-${label}`} x={MARGIN.left + index * cellWidth + cellWidth / 2} y={HEIGHT - 24} textAnchor="middle" fontSize="11" fill="#6b5d4d">
          {label}
        </text>
      ))}
      {yCategories.map((label, index) => (
        <text key={`hm-y-${label}`} x={18} y={MARGIN.top + index * cellHeight + cellHeight / 2 + 4} fontSize="11" fill="#6b5d4d">
          {label}
        </text>
      ))}
      {yCategories.map((yLabel, rowIndex) =>
        xCategories.map((xLabel, colIndex) => {
          const count = table.get(`${xLabel}::${yLabel}`) || 0;
          const intensity = count / maxCount;
          const fill = `rgba(182, 93, 34, ${0.12 + intensity * 0.72})`;
          return (
            <g key={`${xLabel}-${yLabel}`}>
              <title>{`${xLabel} / ${yLabel}: ${count}`}</title>
              <rect
                x={MARGIN.left + colIndex * cellWidth}
                y={MARGIN.top + rowIndex * cellHeight}
                width={cellWidth - 2}
                height={cellHeight - 2}
                fill={fill}
                stroke="#d9c1a7"
              />
              {count > 0 ? (
                <text
                  x={MARGIN.left + colIndex * cellWidth + cellWidth / 2}
                  y={MARGIN.top + rowIndex * cellHeight + cellHeight / 2 + 4}
                  textAnchor="middle"
                  fontSize="12"
                  fill={count / maxCount > 0.45 ? "#fffaf3" : "#3a2d22"}
                >
                  {count}
                </text>
              ) : null}
            </g>
          );
        }),
      )}
    </svg>
  );
}

function drawCorrelationHeatmap({ snapshot, rows }) {
  const numericColumns = collectNumericColumns(snapshot, rows);
  if (numericColumns.length < 2) {
    return renderNoData("No correlation heatmap data", "Need at least two numeric columns.");
  }
  const labels = numericColumns.map((column) => column.header);
  const matrix = numericColumns.map((left) =>
    numericColumns.map((right) => pearsonCorrelation(left.values, right.values) ?? 0),
  );
  const cellSize = Math.min(
    46,
    (WIDTH - MARGIN.left - MARGIN.right) / labels.length,
    (HEIGHT - MARGIN.top - MARGIN.bottom) / labels.length,
  );

  return (
    <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} fontFamily={SVG_FONT_FAMILY}>
      <rect x="0" y="0" width={WIDTH} height={HEIGHT} rx="18" fill="#fffaf3" stroke="#e0ccb4" />
      {axisLabel({ xName: "Numeric columns", yName: "Correlation", subtitle: snapshot.current_graph_type })}
      {renderHorizontalGridLines()}
      {renderYAxisTickLabels({ domainMin: -1, domainMax: 1 })}
      {renderVerticalGridLines(Math.max(labels.length, 4))}
      {renderTopRightSpines()}
      <line x1={MARGIN.left} y1={HEIGHT - MARGIN.bottom} x2={WIDTH - MARGIN.right} y2={HEIGHT - MARGIN.bottom} stroke="#6b5d4d" />
      <line x1={MARGIN.left} y1={MARGIN.top} x2={MARGIN.left} y2={HEIGHT - MARGIN.bottom} stroke="#6b5d4d" />
      {labels.map((label, index) => (
        <text key={`corr-x-${label}`} x={MARGIN.left + index * cellSize + cellSize / 2} y={HEIGHT - 24} textAnchor="middle" fontSize="10" fill="#6b5d4d">
          {label}
        </text>
      ))}
      {labels.map((label, index) => (
        <text key={`corr-y-${label}`} x={18} y={MARGIN.top + index * cellSize + cellSize / 2 + 4} fontSize="10" fill="#6b5d4d">
          {label}
        </text>
      ))}
      {matrix.map((row, rowIndex) =>
        row.map((value, colIndex) => {
          const intensity = Math.abs(value);
          const red = value >= 0 ? 182 : 63;
          const green = value >= 0 ? 93 : 111;
          const blue = value >= 0 ? 34 : 168;
          return (
            <g key={`corr-${rowIndex}-${colIndex}`}>
              <title>{`${labels[colIndex]} / ${labels[rowIndex]}: ${formatNumber(value)}`}</title>
              <rect
                x={MARGIN.left + colIndex * cellSize}
                y={MARGIN.top + rowIndex * cellSize}
                width={cellSize - 2}
                height={cellSize - 2}
                fill={`rgba(${red}, ${green}, ${blue}, ${0.12 + intensity * 0.72})`}
                stroke="#d9c1a7"
              />
              <text
                x={MARGIN.left + colIndex * cellSize + cellSize / 2}
                y={MARGIN.top + rowIndex * cellSize + cellSize / 2 + 4}
                textAnchor="middle"
                fontSize="10"
                fill={intensity > 0.5 ? "#fffaf3" : "#3a2d22"}
              >
                {formatNumber(value)}
              </text>
            </g>
          );
        }),
      )}
    </svg>
  );
}

function calcStats(values) {
  if (!values || values.length === 0) {
    return null;
  }
  const sorted = [...values].sort((a, b) => a - b);
  const n = sorted.length;
  const mean = sorted.reduce((sum, value) => sum + value, 0) / n;
  const median = sorted[Math.floor((n - 1) / 2)];
  const q1 = sorted[Math.floor((n - 1) * 0.25)];
  const q3 = sorted[Math.floor((n - 1) * 0.75)];
  const iqr = q3 - q1;
  const lower = Math.max(sorted[0], q1 - 1.5 * iqr);
  const upper = Math.min(sorted[n - 1], q3 + 1.5 * iqr);
  return { min: sorted[0], max: sorted[n - 1], mean, median, q1, q3, lower, upper, n };
}

function buildLinearScale(domainMin, domainMax, rangeMin, rangeMax) {
  const safeMin = Number.isFinite(domainMin) ? domainMin : 0;
  const safeMax = Number.isFinite(domainMax) ? domainMax : 1;
  const span = safeMax - safeMin;
  const safeSpan = Math.abs(span) < 1e-9 ? 1 : span;
  return (value) => rangeMin + ((value - safeMin) / safeSpan) * (rangeMax - rangeMin);
}

function transformLog10Value(value) {
  return Number.isFinite(value) && value > 0 ? Math.log10(value) : null;
}

function buildYAxisValues(values, yLogScale) {
  if (!yLogScale) {
    return values.filter((value) => Number.isFinite(value));
  }
  return values.map(transformLog10Value).filter((value) => value !== null);
}

function formatYAxisLabel(label, yLogScale) {
  return yLogScale ? `${label} (log10)` : label;
}

function buildPointCloud(rows, snapshot, xName, yName, subgroupName) {
  const xIndex = getColumnIndex(snapshot, xName);
  const yIndex = getColumnIndex(snapshot, yName);
  const subgroupIndex = subgroupName ? getColumnIndex(snapshot, subgroupName) : -1;
  if (xIndex < 0 || yIndex < 0) {
    return null;
  }

  const points = [];
  const categories = [];
  const numericXValues = [];
  const numericYValues = [];

  for (const row of rows) {
    const rawX = row[xIndex] ?? "";
    const rawY = row[yIndex] ?? "";
    const yValue = parseNumber(rawY);
    if (yValue === null) {
      continue;
    }
    const xValue = parseNumber(rawX);
    const categoryLabel = String(rawX ?? "").trim() || "(empty)";
    const seriesLabel =
      subgroupIndex >= 0 ? String(row[subgroupIndex] ?? "").trim() || "(empty)" : "All";

    points.push({
      xValue,
      yValue,
      categoryLabel,
      seriesLabel,
      rawX: String(rawX ?? ""),
      rawY: String(rawY ?? ""),
    });
    if (!categories.includes(categoryLabel)) {
      categories.push(categoryLabel);
    }
    if (xValue !== null) {
      numericXValues.push(xValue);
    }
    numericYValues.push(yValue);
  }

  if (points.length === 0) {
    return null;
  }

  return {
    points,
    categories,
    numericXValues,
    numericYValues,
    xName,
    yName,
    subgroupName,
  };
}

function renderNoData(label, body) {
  return (
    <div className="graph-empty" style={{ fontFamily: SVG_FONT_FAMILY }}>
      <strong>{label}</strong>
      <span>{body}</span>
    </div>
  );
}

function wrapAnnotationText(text, limit = 48) {
  const words = text.split(/\s+/).filter(Boolean);
  const lines = [];
  let current = "";

  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (next.length > limit && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  }

  if (current) {
    lines.push(current);
  }
  return lines.slice(0, 4);
}

function renderAnnotationOverlay(summary) {
  if (!summary) {
    return null;
  }
  const lines = wrapAnnotationText(summary);
  return (
    <div className="graph-annotation-float">
      <strong>Post-hoc</strong>
      {lines.map((line, index) => (
        <span key={`annotation-${index}`}>{line}</span>
      ))}
    </div>
  );
}

function parseAnnotationSummary(summary) {
  if (!summary) {
    return [];
  }
  const colonIndex = summary.indexOf(":");
  if (colonIndex < 0) {
    return [];
  }
  return summary
    .slice(colonIndex + 1)
    .split(",")
    .map((item) => item.trim())
    .map((item) => {
      const match = item.match(/^(.+?)\s*(?:>|!=)\s*(.+?)$/);
      if (!match) {
        return null;
      }
      return {
        left: match[1].trim(),
        right: match[2].trim(),
      };
    })
    .filter(Boolean);
}

function renderPairAnnotations({ annotations, categories, xScale, baseY, color = "#8f4617" }) {
  if (!annotations.length) {
    return null;
  }
  const categoryPositions = new Map(categories.map((category, index) => [category, xScale(index)]));
  const usedLevels = [];
  return annotations.map((annotation, index) => {
    const x1 = categoryPositions.get(annotation.left);
    const x2 = categoryPositions.get(annotation.right);
    if (!Number.isFinite(x1) || !Number.isFinite(x2)) {
      return null;
    }
    const levelIndex = usedLevels.findIndex((level) => Math.abs(level - x1) > 40 && Math.abs(level - x2) > 40);
    const yOffset = 12 + (levelIndex >= 0 ? levelIndex : usedLevels.length) * 14;
    if (levelIndex < 0) {
      usedLevels.push((x1 + x2) / 2);
    }
    const y = baseY - yOffset;
    return (
      <g key={`annotation-${annotation.left}-${annotation.right}-${index}`}>
        <line x1={x1} y1={y} x2={x2} y2={y} stroke={color} strokeWidth="1.8" opacity="0.85" />
        <line x1={x1} y1={y} x2={x1} y2={y + 6} stroke={color} strokeWidth="1.8" opacity="0.85" />
        <line x1={x2} y1={y} x2={x2} y2={y + 6} stroke={color} strokeWidth="1.8" opacity="0.85" />
        <text x={(x1 + x2) / 2} y={y - 3} textAnchor="middle" fontSize="12" fill={color} fontWeight="700">
          *
        </text>
      </g>
    );
  });
}

function axisLabel({ xName, yName, subtitle }) {
  return (
    <>
      <text x={MARGIN.left} y={22} fill="#3a2d22" fontSize="16" fontWeight="700">
        {subtitle}
      </text>
      <text x={MARGIN.left} y={HEIGHT - 6} fill="#6b5d4d" fontSize="12">
        {xName}
      </text>
      <text x={18} y={MARGIN.top + 14} fill="#6b5d4d" fontSize="12">
        {yName}
      </text>
    </>
  );
}

function renderHorizontalGridLines(count = 4) {
  return Array.from({ length: count }, (_, index) => {
    const y = MARGIN.top + ((HEIGHT - MARGIN.top - MARGIN.bottom) * (index + 1)) / (count + 1);
    const isMajorLine = index === Math.floor(count / 2);
    return (
      <line
        key={`grid-${index}`}
        x1={MARGIN.left}
        y1={y}
        x2={WIDTH - MARGIN.right}
        y2={y}
        stroke={isMajorLine ? "#c7b08e" : "#dcc9b2"}
        strokeDasharray={isMajorLine ? "6 4" : "4 4"}
        strokeWidth={isMajorLine ? "1.2" : "1"}
        opacity={isMajorLine ? "0.6" : "0.4"}
      />
    );
  });
}

function buildTickValues(domainMin, domainMax, count = 4) {
  const safeMin = Number.isFinite(domainMin) ? domainMin : 0;
  const safeMax = Number.isFinite(domainMax) ? domainMax : 1;
  const span = safeMax - safeMin;
  return Array.from({ length: count }, (_, index) => safeMax - (span * (index + 1)) / (count + 1));
}

function renderYAxisTickLabels({
  domainMin,
  domainMax,
  count = 4,
  formatter = formatNumber,
  logScale = false,
  x = MARGIN.left - 10,
  fontSize = 11,
  anchor = "end",
}) {
  return buildTickValues(domainMin, domainMax, count).map((value, index) => {
    const labelValue = logScale ? Math.pow(10, value) : value;
    return (
      <text
        key={`y-tick-${index}`}
        x={x}
        y={MARGIN.top + ((HEIGHT - MARGIN.top - MARGIN.bottom) * (index + 1)) / (count + 1) + 4}
        textAnchor={anchor}
        fontSize={fontSize}
        fill="#6b5d4d"
      >
        {formatter(labelValue)}
      </text>
    );
  });
}

function renderXAxisTickLabels({
  domainMin,
  domainMax,
  count = 4,
  formatter = formatNumber,
  y = HEIGHT - 24,
  fontSize = 11,
  scale = null,
}) {
  const values = buildTickValues(domainMin, domainMax, count).reverse();
  return values.map((value, index) => {
    const x = scale ? scale(value) : MARGIN.left + ((WIDTH - MARGIN.left - MARGIN.right) * (index + 1)) / (count + 1);
    return (
      <text key={`x-tick-${index}`} x={x} y={y} textAnchor="middle" fontSize={fontSize} fill="#6b5d4d">
        {formatter(value)}
      </text>
    );
  });
}

function renderVerticalGridLines(count = 4) {
  return Array.from({ length: count }, (_, index) => {
    const x = MARGIN.left + ((WIDTH - MARGIN.left - MARGIN.right) * (index + 1)) / (count + 1);
    const isMajorLine = index === Math.floor(count / 2);
    return (
      <line
        key={`vgrid-${index}`}
        x1={x}
        y1={MARGIN.top}
        x2={x}
        y2={HEIGHT - MARGIN.bottom}
        stroke={isMajorLine ? "#c7b08e" : "#dcc9b2"}
        strokeDasharray={isMajorLine ? "6 4" : "4 4"}
        strokeWidth={isMajorLine ? "1.1" : "1"}
        opacity={isMajorLine ? "0.45" : "0.28"}
      />
    );
  });
}

function renderTopRightSpines() {
  return (
    <>
      <line x1={MARGIN.left} y1={MARGIN.top} x2={WIDTH - MARGIN.right} y2={MARGIN.top} stroke="#ccb79d" opacity="0.45" />
      <line x1={WIDTH - MARGIN.right} y1={MARGIN.top} x2={WIDTH - MARGIN.right} y2={HEIGHT - MARGIN.bottom} stroke="#ccb79d" opacity="0.45" />
    </>
  );
}

function renderPrimaryAxes() {
  return (
    <>
      <line x1={MARGIN.left} y1={HEIGHT - MARGIN.bottom} x2={WIDTH - MARGIN.right} y2={HEIGHT - MARGIN.bottom} stroke="#6b5d4d" />
      <line x1={MARGIN.left} y1={MARGIN.top} x2={MARGIN.left} y2={HEIGHT - MARGIN.bottom} stroke="#6b5d4d" />
    </>
  );
}

const MARKER_SHAPES = ["circle", "square", "diamond", "triangle"];

function renderMarker({
  x,
  y,
  type,
  color,
  radius = 4,
  fill = color,
  stroke = color,
  strokeWidth = 1.2,
  opacity = 1,
  title = "",
}) {
  const titleNode = title ? <title>{title}</title> : null;
  if (type === "square") {
    return (
      <g>
        {titleNode}
        <rect x={x - radius} y={y - radius} width={radius * 2} height={radius * 2} fill={fill} stroke={stroke} strokeWidth={strokeWidth} opacity={opacity} />
      </g>
    );
  }
  if (type === "diamond") {
    return (
      <g>
        {titleNode}
        <path d={`M ${x} ${y - radius} L ${x + radius} ${y} L ${x} ${y + radius} L ${x - radius} ${y} Z`} fill={fill} stroke={stroke} strokeWidth={strokeWidth} opacity={opacity} />
      </g>
    );
  }
  if (type === "triangle") {
    const h = radius * 1.15;
    return (
      <g>
        {titleNode}
        <path d={`M ${x} ${y - h} L ${x + radius} ${y + h / 2} L ${x - radius} ${y + h / 2} Z`} fill={fill} stroke={stroke} strokeWidth={strokeWidth} opacity={opacity} />
      </g>
    );
  }
  return (
    <g>
      {titleNode}
      <circle cx={x} cy={y} r={radius} fill={fill} stroke={stroke} strokeWidth={strokeWidth} opacity={opacity} />
    </g>
  );
}

function formatPointTitle({ seriesLabel, xLabel, yLabel, extra = "" }) {
  return [seriesLabel, xLabel, yLabel, extra].filter(Boolean).join(" | ");
}

function shouldAnnotateIndividualPoints(points) {
  return points.length > 0 && points.length <= 12;
}

function renderPointValueLabel({ x, y, label, anchor = "middle" }) {
  if (!label) {
    return null;
  }
  return (
    <text x={x} y={y} textAnchor={anchor} fontSize="10" fill="#5b4b3f">
      {label}
    </text>
  );
}

function drawPointPlot({
  snapshot,
  rows,
  xName,
  yName,
  subgroupName,
  includeLine = false,
  summaryOnly = false,
  yLogScale = false,
}) {
  const cloud = buildPointCloud(rows, snapshot, xName, yName, subgroupName);
  if (!cloud) {
    return renderNoData("No point data", "Choose columns with numeric values.");
  }

  const categorical = cloud.numericXValues.length < cloud.points.length * 0.5;
  const xDomain = categorical
    ? { min: 0, max: cloud.categories.length - 1 }
    : {
        min: Math.min(...cloud.numericXValues),
        max: Math.max(...cloud.numericXValues),
      };
  const yValues = buildYAxisValues(cloud.numericYValues, yLogScale);
  if (yValues.length === 0) {
    return renderNoData("No point data", "Log scale needs positive numeric Y values.");
  }
  const yDomain = {
    min: Math.min(...yValues),
    max: Math.max(...yValues),
  };
  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;
  const xScale = buildLinearScale(xDomain.min, xDomain.max, MARGIN.left, MARGIN.left + plotWidth);
  const yScale = buildLinearScale(yDomain.min, yDomain.max, HEIGHT - MARGIN.bottom, MARGIN.top);

  const seriesGroups = new Map();
  for (const point of cloud.points) {
    const key = point.seriesLabel;
    if (!seriesGroups.has(key)) {
      seriesGroups.set(key, []);
    }
    seriesGroups.get(key).push(point);
  }
  const annotatePoints = shouldAnnotateIndividualPoints(cloud.points);

  return (
    <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} fontFamily={SVG_FONT_FAMILY}>
      <rect x="0" y="0" width={WIDTH} height={HEIGHT} rx="18" fill="#fffaf3" stroke="#e0ccb4" />
      {axisLabel({ xName, yName: formatYAxisLabel(yName, yLogScale), subtitle: `${snapshot.current_graph_type}` })}
      {renderHorizontalGridLines()}
      {renderYAxisTickLabels({ domainMin: yDomain.min, domainMax: yDomain.max, logScale: yLogScale })}
      {renderVerticalGridLines(categorical ? Math.max(cloud.categories.length, 4) : 4)}
      {!categorical ? renderXAxisTickLabels({ domainMin: xDomain.min, domainMax: xDomain.max, scale: xScale }) : null}
      <line
        x1={MARGIN.left}
        y1={HEIGHT - MARGIN.bottom}
        x2={WIDTH - MARGIN.right}
        y2={HEIGHT - MARGIN.bottom}
        stroke="#6b5d4d"
      />
      <line
        x1={MARGIN.left}
        y1={MARGIN.top}
        x2={MARGIN.left}
        y2={HEIGHT - MARGIN.bottom}
        stroke="#6b5d4d"
      />

      {categorical &&
        cloud.categories.map((category, index) => {
          const x = xScale(index);
          return (
            <text
              key={`x-label-${category}`}
              x={x}
              y={HEIGHT - 24}
              textAnchor="middle"
              fontSize="12"
              fill="#6b5d4d"
            >
              {category}
            </text>
          );
        })}

      {!categorical &&
        cloud.points
          .filter((_, index) => index < 10)
          .map((point, index) => (
            <text
              key={`x-num-${index}`}
              x={xScale(point.xValue ?? 0)}
              y={HEIGHT - 24}
              textAnchor="middle"
              fontSize="12"
              fill="#6b5d4d"
            >
              {formatNumber(point.xValue ?? 0)}
            </text>
          ))}

      {[...seriesGroups.entries()].map(([seriesLabel, points], seriesIndex) => {
        const color = SERIES_COLORS[seriesIndex % SERIES_COLORS.length];
        const catMeans = new Map();
        points.forEach((point) => {
          const key = categorical ? point.categoryLabel : String(point.xValue ?? "");
          if (!catMeans.has(key)) {
            catMeans.set(key, []);
          }
          catMeans.get(key).push(point.yValue);
        });
        const summaryPoints = [...catMeans.entries()].map(([key, values], index) => {
          const transformedValues = yLogScale ? buildYAxisValues(values, true) : values;
          if (transformedValues.length === 0) {
            return null;
          }
          const mean = transformedValues.reduce((sum, value) => sum + value, 0) / transformedValues.length;
          const x = categorical ? xScale(cloud.categories.indexOf(key)) : xScale(Number(key));
          return { x, y: yScale(mean), mean, label: key, index };
        }).filter(Boolean);

        return (
          <g key={seriesLabel}>
            {!summaryOnly &&
              points.map((point, index) => {
                const x = categorical
                  ? xScale(cloud.categories.indexOf(point.categoryLabel)) +
                    ((seriesIndex - (seriesGroups.size - 1) / 2) * 10)
                  : xScale(point.xValue ?? 0);
                const yValue = yLogScale ? transformLog10Value(point.yValue) : point.yValue;
                if (yValue === null) {
                  return null;
                }
                const y = yScale(yValue);
                const radius = includeLine ? 4 : 3.5;
                const marker = MARKER_SHAPES[seriesIndex % MARKER_SHAPES.length];
                return (
                  <g key={`${seriesLabel}-${index}`}>
                    {renderMarker({
                      x,
                      y,
                      type: marker,
                      color,
                      radius,
                      stroke: "#fffaf3",
                      strokeWidth: 1.25,
                      opacity: 0.88,
                      title: formatPointTitle({
                        seriesLabel,
                        xLabel: `${xName}: ${point.rawX || formatNumber(point.xValue ?? 0)}`,
                        yLabel: `${yName}: ${formatNumber(point.yValue)}`,
                        extra: point.categoryLabel !== point.rawX ? `Category: ${point.categoryLabel}` : "",
                      }),
                    })}
                    {annotatePoints
                      ? renderPointValueLabel({
                          x,
                          y: y - 8,
                          label: formatNumber(point.yValue),
                        })
                      : null}
                  </g>
                );
              })}

            {(includeLine || summaryOnly) &&
              summaryPoints.length > 1 && (
                <polyline
                  fill="none"
                  stroke={color}
                  strokeWidth="2.5"
                  points={summaryPoints.map((point) => `${point.x},${point.y}`).join(" ")}
                  opacity="0.9"
                />
              )}

            {summaryPoints.map((point) => (
              <g key={`${seriesLabel}-${point.label}`}>
                <title>{formatPointTitle({
                  seriesLabel,
                  xLabel: `${xName}: ${point.label}`,
                  yLabel: `${yName}: ${formatNumber(point.mean)}`,
                })}</title>
                <circle
                  cx={point.x}
                  cy={point.y}
                  r={summaryOnly ? 6 : 5}
                  fill="#fffaf3"
                  stroke={color}
                  strokeWidth="2"
                />
              </g>
            ))}
          </g>
        );
      })}
    </svg>
  );
}

function drawBoxPlot({ snapshot, rows, xName, yName, subgroupName, annotationSummary, yLogScale = false }) {
  const cloud = collectSeriesRows(rows, snapshot, xName, yName, subgroupName);
  if (!cloud) {
    return renderNoData("No box plot data", "Choose a categorical X column and numeric Y column.");
  }
  const summary = summarizeCategorySeries(cloud.seriesMap, cloud.categories);
  const allValues = [...summary.values()].flatMap((items) =>
    items.flatMap((item) => (yLogScale ? buildYAxisValues(item.values || [], true) : item.values || [])),
  );
  if (allValues.length === 0) {
    return renderNoData("No box plot data", "Log scale needs positive numeric Y values.");
  }
  const yDomain = {
    min: Math.min(...allValues),
    max: Math.max(...allValues),
  };
  const xScale = buildLinearScale(0, Math.max(cloud.categories.length - 1, 1), MARGIN.left + 30, WIDTH - MARGIN.right - 30);
  const yScale = buildLinearScale(yDomain.min, yDomain.max, HEIGHT - MARGIN.bottom, MARGIN.top);
  const boxWidth = 46;
  const color = SERIES_COLORS[0];
  const annotations = parseAnnotationSummary(annotationSummary);

  return (
    <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} fontFamily={SVG_FONT_FAMILY}>
      <rect x="0" y="0" width={WIDTH} height={HEIGHT} rx="18" fill="#fffaf3" stroke="#e0ccb4" />
      {axisLabel({ xName, yName: formatYAxisLabel(yName, yLogScale), subtitle: snapshot.current_graph_type })}
      {renderHorizontalGridLines()}
      {renderYAxisTickLabels({ domainMin: yDomain.min, domainMax: yDomain.max, logScale: yLogScale })}
      {renderVerticalGridLines(Math.max(cloud.categories.length, 4))}
      {renderTopRightSpines()}
      <line x1={MARGIN.left} y1={HEIGHT - MARGIN.bottom} x2={WIDTH - MARGIN.right} y2={HEIGHT - MARGIN.bottom} stroke="#6b5d4d" />
      <line x1={MARGIN.left} y1={MARGIN.top} x2={MARGIN.left} y2={HEIGHT - MARGIN.bottom} stroke="#6b5d4d" />
      {cloud.categories.map((category, index) => {
        const stats = summary.get("All")?.find((entry) => entry.category === category) ||
          [...summary.values()][0].find((entry) => entry.category === category);
        if (!stats) {
          return null;
        }
        const x = xScale(index);
        const q = calcStats(yLogScale ? buildYAxisValues(stats.values, true) : stats.values);
        if (!q) {
          return null;
        }
        return (
          <g key={category}>
            <title>{formatPointTitle({
              seriesLabel: category,
              xLabel: xName,
              yLabel: `${yName}: lower ${formatNumber(q.lower)}, q1 ${formatNumber(q.q1)}, median ${formatNumber(q.median)}, q3 ${formatNumber(q.q3)}, upper ${formatNumber(q.upper)}`,
            })}</title>
            <line x1={x} x2={x} y1={yScale(q.lower)} y2={yScale(q.upper)} stroke={color} strokeWidth="2" />
            <rect
              x={x - boxWidth / 2}
              y={yScale(q.q3)}
              width={boxWidth}
              height={Math.max(1, yScale(q.q1) - yScale(q.q3))}
              fill="#dca66d"
              opacity="0.7"
              stroke={color}
            />
            <line x1={x - boxWidth / 2} x2={x + boxWidth / 2} y1={yScale(q.median)} y2={yScale(q.median)} stroke="#6b5d4d" strokeWidth="2" />
            <circle cx={x} cy={yScale(q.mean)} r="4" fill="#fffaf3" stroke={color} strokeWidth="2" />
            <line x1={x - 16} x2={x + 16} y1={yScale(q.lower)} y2={yScale(q.lower)} stroke={color} />
            <line x1={x - 16} x2={x + 16} y1={yScale(q.upper)} y2={yScale(q.upper)} stroke={color} />
            <text x={x} y={HEIGHT - 24} textAnchor="middle" fontSize="12" fill="#6b5d4d">{category}</text>
          </g>
        );
      })}
      {renderPairAnnotations({
        annotations,
        categories: cloud.categories,
        xScale,
        baseY: MARGIN.top + 26,
        color: "#7b4aa5",
      })}
    </svg>
  );
}

function drawViolinPlot({ snapshot, rows, xName, yName, subgroupName, annotationSummary, yLogScale = false }) {
  const cloud = collectSeriesRows(rows, snapshot, xName, yName, subgroupName);
  if (!cloud) {
    return renderNoData("No violin data", "Choose a categorical X column and numeric Y column.");
  }
  const summary = summarizeCategorySeries(cloud.seriesMap, cloud.categories);
  const allValues = [...summary.values()].flatMap((items) =>
    items.flatMap((item) => (yLogScale ? buildYAxisValues(item.values || [], true) : item.values || [])),
  );
  if (allValues.length === 0) {
    return renderNoData("No violin data", "Log scale needs positive numeric Y values.");
  }

  const yDomain = {
    min: Math.min(...allValues),
    max: Math.max(...allValues),
  };
  const xScale = buildLinearScale(0, Math.max(cloud.categories.length - 1, 1), MARGIN.left + 36, WIDTH - MARGIN.right - 36);
  const yScale = buildLinearScale(yDomain.min, yDomain.max, HEIGHT - MARGIN.bottom, MARGIN.top);
  const color = SERIES_COLORS[1];
  const annotations = parseAnnotationSummary(annotationSummary);

  return (
    <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} fontFamily={SVG_FONT_FAMILY}>
      <rect x="0" y="0" width={WIDTH} height={HEIGHT} rx="18" fill="#fffaf3" stroke="#e0ccb4" />
      {axisLabel({ xName, yName: formatYAxisLabel(yName, yLogScale), subtitle: snapshot.current_graph_type })}
      {renderHorizontalGridLines()}
      {renderYAxisTickLabels({ domainMin: yDomain.min, domainMax: yDomain.max, logScale: yLogScale })}
      {renderVerticalGridLines(Math.max(cloud.categories.length, 4))}
      {renderTopRightSpines()}
      <line x1={MARGIN.left} y1={HEIGHT - MARGIN.bottom} x2={WIDTH - MARGIN.right} y2={HEIGHT - MARGIN.bottom} stroke="#6b5d4d" />
      <line x1={MARGIN.left} y1={MARGIN.top} x2={MARGIN.left} y2={HEIGHT - MARGIN.bottom} stroke="#6b5d4d" />
      {cloud.categories.map((category, index) => {
        const stats = [...summary.values()][0].find((entry) => entry.category === category);
        if (!stats || stats.values.length === 0) {
          return null;
        }
        const x = xScale(index);
        const bins = 18;
        const violinValues = yLogScale ? buildYAxisValues(stats.values, true) : stats.values;
        if (violinValues.length === 0) {
          return null;
        }
        const min = yLogScale ? Math.min(...violinValues) : stats.min;
        const max = yLogScale ? Math.max(...violinValues) : stats.max;
        const span = Math.max(max - min, 1e-9);
        const counts = Array.from({ length: bins }, () => 0);
        violinValues.forEach((value) => {
          let bin = Math.floor(((value - min) / span) * bins);
          if (bin >= bins) bin = bins - 1;
          if (bin < 0) bin = 0;
          counts[bin] += 1;
        });
        const maxCount = Math.max(...counts, 1);
        const halfWidth = 26;
        const points = [];
        counts.forEach((count, binIndex) => {
          const ratio = count / maxCount;
          const value = min + ((binIndex + 0.5) / bins) * span;
          const y = yScale(value);
          const width = halfWidth * ratio;
          points.push(`${x - width},${y}`);
        });
        counts.slice().reverse().forEach((count, reverseIndex) => {
          const binIndex = bins - 1 - reverseIndex;
          const ratio = count / maxCount;
          const value = min + ((binIndex + 0.5) / bins) * span;
          const y = yScale(value);
          const width = halfWidth * ratio;
          points.push(`${x + width},${y}`);
        });

        return (
          <g key={category}>
            <title>{formatPointTitle({
              seriesLabel: category,
              xLabel: xName,
              yLabel: `${yName}: mean ${formatNumber(stats.mean)}`,
              extra: `range ${formatNumber(min)} - ${formatNumber(max)}`,
            })}</title>
            <path d={`M ${points.join(" L ")} Z`} fill={color} opacity="0.45" stroke={color} strokeWidth="1.5" />
            <circle cx={x} cy={yScale(stats.mean)} r="4" fill="#fffaf3" stroke={color} strokeWidth="2" />
            <text x={x} y={HEIGHT - 24} textAnchor="middle" fontSize="12" fill="#6b5d4d">{category}</text>
          </g>
        );
      })}
      {renderPairAnnotations({
        annotations,
        categories: cloud.categories,
        xScale,
        baseY: MARGIN.top + 26,
        color: "#3f6fa8",
      })}
    </svg>
  );
}

function drawPairedScatter({ snapshot, rows, xName, yName, yLogScale = false }) {
  const xIndex = getColumnIndex(snapshot, xName);
  const yIndex = getColumnIndex(snapshot, yName);
  if (xIndex < 0 || yIndex < 0) {
    return renderNoData("No paired data", "Choose two numeric columns.");
  }

  const pairs = rows
    .map((row) => {
      const x = parseNumber(row[xIndex]);
      const y = parseNumber(row[yIndex]);
      if (x === null || y === null) {
        return null;
      }
      if (yLogScale && (x <= 0 || y <= 0)) {
        return null;
      }
      return {
        x: yLogScale ? Math.log10(x) : x,
        y: yLogScale ? Math.log10(y) : y,
      };
    })
    .filter(Boolean);

  if (pairs.length === 0) {
    return renderNoData("No paired data", "Choose two numeric columns.");
  }

  const values = pairs.flatMap((pair) => [pair.x, pair.y]);
  const yDomain = {
    min: Math.min(...values),
    max: Math.max(...values),
  };
  const yScale = buildLinearScale(yDomain.min, yDomain.max, HEIGHT - MARGIN.bottom, MARGIN.top);
  const leftX = MARGIN.left + 110;
  const rightX = WIDTH - MARGIN.right - 110;
  const annotatePoints = shouldAnnotateIndividualPoints(pairs);

  return (
    <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} fontFamily={SVG_FONT_FAMILY}>
      <rect x="0" y="0" width={WIDTH} height={HEIGHT} rx="18" fill="#fffaf3" stroke="#e0ccb4" />
      <text x={MARGIN.left} y={22} fill="#3a2d22" fontSize="16" fontWeight="700">
        {yLogScale ? "Paired Scatter (log10)" : "Paired Scatter"}
      </text>
      <text x={WIDTH / 2} y={22} textAnchor="middle" fill="#6b5d4d" fontSize="11">
        Shared vertical scale for both columns
      </text>
      {renderTopRightSpines()}
      {renderYAxisTickLabels({ domainMin: yDomain.min, domainMax: yDomain.max, logScale: yLogScale, x: leftX - 12 })}
      {renderYAxisTickLabels({ domainMin: yDomain.min, domainMax: yDomain.max, logScale: yLogScale, x: rightX + 12, anchor: "start" })}
      <text x={leftX} y={MARGIN.top + 16} textAnchor="middle" fill="#3f6fa8" fontSize="11" fontWeight="700">
        X values
      </text>
      <text x={leftX} y={MARGIN.top + 30} textAnchor="middle" fill="#6b5d4d" fontSize="11">
        {xName}
      </text>
      <text x={rightX} y={MARGIN.top + 16} textAnchor="middle" fill="#b65d22" fontSize="11" fontWeight="700">
        Y values
      </text>
      <text x={rightX} y={MARGIN.top + 30} textAnchor="middle" fill="#6b5d4d" fontSize="11">
        {yName}
      </text>
      <line x1={leftX} y1={MARGIN.top} x2={leftX} y2={HEIGHT - MARGIN.bottom} stroke="#6b5d4d" />
      <line x1={rightX} y1={MARGIN.top} x2={rightX} y2={HEIGHT - MARGIN.bottom} stroke="#6b5d4d" />
      <text x={leftX} y={HEIGHT - 24} textAnchor="middle" fontSize="12" fill="#6b5d4d">
        {xName}
      </text>
      <text x={rightX} y={HEIGHT - 24} textAnchor="middle" fontSize="12" fill="#6b5d4d">
        {yName}
      </text>
      {pairs.map((pair, index) => {
        const y1 = yScale(pair.x);
        const y2 = yScale(pair.y);
        return (
          <g key={`pair-${index}`}>
            <line x1={leftX} x2={rightX} y1={y1} y2={y2} stroke="#b65d22" strokeWidth="1.5" opacity="0.45" />
            {renderMarker({
              x: leftX,
              y: y1,
              type: "circle",
              color: "#3f6fa8",
              radius: 4,
              stroke: "#fffaf3",
              strokeWidth: 1.25,
              opacity: 1,
              title: `${xName}: ${formatNumber(pair.x)}`,
            })}
            {renderMarker({
              x: rightX,
              y: y2,
              type: "diamond",
              color: "#b65d22",
              radius: 4,
              stroke: "#fffaf3",
              strokeWidth: 1.25,
              opacity: 1,
              title: `${yName}: ${formatNumber(pair.y)}`,
            })}
            {annotatePoints
              ? renderPointValueLabel({
                  x: leftX - 10,
                  y: y1 - 6,
                  label: formatNumber(pair.x),
                  anchor: "end",
                })
              : null}
            {annotatePoints
              ? renderPointValueLabel({
                  x: rightX + 10,
                  y: y2 - 6,
                  label: formatNumber(pair.y),
                  anchor: "start",
                })
              : null}
          </g>
        );
      })}
    </svg>
  );
}

function GraphViewImpl({ snapshot, graphType, yLogScale = false }, ref) {
  const rows = getVisibleRows(snapshot);
  const xName = snapshot.x_column || "";
  const yName = snapshot.y_column || "";
  const subgroupName = snapshot.subgroup_column || "";
  const annotationSummary = snapshot.graph_annotation_summary || "";

  let content;
  switch (graphType) {
    case "Bar Chart":
      content = drawBarPlot({ snapshot, rows, xName, yName, subgroupName, annotationSummary });
      break;
    case "Count Plot":
      content = drawCountPlot({ snapshot, rows, xName, subgroupName, annotationSummary });
      break;
    case "Stacked Bar":
      content = drawStackedBarPlot({ snapshot, rows, xName, subgroupName, normalized: false, annotationSummary });
      break;
    case "100% Stacked Bar":
      content = drawStackedBarPlot({ snapshot, rows, xName, subgroupName, normalized: true, annotationSummary });
      break;
    case "Scatter Plot":
      content = drawPointPlot({ snapshot, rows, xName, yName, subgroupName, includeLine: false, summaryOnly: false, yLogScale });
      break;
    case "Summary Scatter":
      content = drawPointPlot({ snapshot, rows, xName, yName, subgroupName, includeLine: true, summaryOnly: true, yLogScale });
      break;
    case "Point Plot":
      content = drawPointPlot({ snapshot, rows, xName, yName, subgroupName, includeLine: false, summaryOnly: true, yLogScale });
      break;
    case "Line Plot":
      content = drawPointPlot({ snapshot, rows, xName, yName, subgroupName, includeLine: true, summaryOnly: true, yLogScale });
      break;
    case "Box Plot":
      content = drawBoxPlot({ snapshot, rows, xName, yName, subgroupName, annotationSummary, yLogScale });
      break;
    case "Violin Plot":
      content = drawViolinPlot({ snapshot, rows, xName, yName, subgroupName, annotationSummary, yLogScale });
      break;
    case "Paired Scatter":
      content = drawPairedScatter({ snapshot, rows, xName, yName, yLogScale });
      break;
    case "Histogram":
      content = drawHistogram({ snapshot, rows, xName });
      break;
    case "Heatmap":
      content = drawHeatmap({ snapshot, rows, xName, yName });
      break;
    case "Mosaic Plot":
      content = drawHeatmap({ snapshot, rows, xName, yName });
      break;
    case "Proportion Plot":
      content = drawStackedBarPlot({ snapshot, rows, xName, subgroupName, normalized: true });
      break;
    case "Correlation Heatmap":
      content = drawCorrelationHeatmap({ snapshot, rows });
      break;
    default:
      content = renderNoData(
        graphType || "No graph type",
        "Choose a supported graph type from the controls.",
      );
      break;
  }

  return (
    <div className="graph-svg-wrap graph-stage" ref={ref}>
      {renderAnnotationOverlay(snapshot.graph_annotation_summary)}
      {content}
    </div>
  );
}

export const GraphView = forwardRef(GraphViewImpl);
