import { ChartJSNodeCanvas } from 'chartjs-node-canvas';
import type { ChartConfiguration } from 'chart.js';
import type { ChartType } from '../types/schemas.js';

const width = 800;
const height = 480;

// Lazy initialization of chart canvas
let chartJSNodeCanvas: ChartJSNodeCanvas | null = null;

function getChartCanvas(): ChartJSNodeCanvas {
  if (!chartJSNodeCanvas) {
    chartJSNodeCanvas = new ChartJSNodeCanvas({
      width,
      height,
      backgroundColour: 'white',
    });
  }
  return chartJSNodeCanvas;
}

/**
 * Generate a chart and return as base64-encoded PNG.
 */
export async function generateChart(
  data: Record<string, number>,
  title: string,
  chartType: ChartType
): Promise<string> {
  const labels = Object.keys(data);
  const values = Object.values(data);

  const config = buildChartConfig(chartType, labels, values, title);
  const canvas = getChartCanvas();
  const imageBuffer = await canvas.renderToBuffer(config);
  const base64 = imageBuffer.toString('base64');
  return `data:image/png;base64,${base64}`;
}

function buildChartConfig(
  chartType: ChartType,
  labels: string[],
  values: number[],
  title: string
): ChartConfiguration {
  const baseOptions = {
    responsive: false,
    plugins: {
      title: {
        display: true,
        text: title,
        font: { size: 16, weight: 'bold' as const },
      },
      legend: {
        display: chartType === 'pie',
      },
    },
  };

  switch (chartType) {
    case 'bar':
      return {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label: 'Value',
              data: values,
              backgroundColor: generateColors(labels.length),
              borderColor: 'rgba(0, 0, 0, 0.1)',
              borderWidth: 1,
            },
          ],
        },
        options: baseOptions,
      };

    case 'line':
      return {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'Value',
              data: values,
              borderColor: '#2E86AB',
              backgroundColor: 'rgba(46, 134, 171, 0.3)',
              fill: true,
              tension: 0.1,
            },
          ],
        },
        options: baseOptions,
      };

    case 'pie':
      return {
        type: 'pie',
        data: {
          labels,
          datasets: [
            {
              data: values,
              backgroundColor: generateColors(labels.length),
            },
          ],
        },
        options: baseOptions,
      };

    case 'scatter':
      return {
        type: 'scatter',
        data: {
          datasets: [
            {
              label: 'Values',
              data: labels.map((_, i) => ({ x: i, y: values[i] ?? 0 })),
              backgroundColor: generateColors(labels.length),
              pointRadius: 8,
            },
          ],
        },
        options: baseOptions,
      };

    case 'histogram':
      // Histogram is represented as a bar chart in Chart.js
      return {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label: 'Frequency',
              data: values,
              backgroundColor: '#2E86AB',
              borderColor: 'rgba(0, 0, 0, 0.5)',
              borderWidth: 1,
            },
          ],
        },
        options: {
          ...baseOptions,
          plugins: {
            ...baseOptions.plugins,
            legend: { display: false },
          },
        },
      };

    default:
      // Default to bar chart
      return buildChartConfig('bar', labels, values, title);
  }
}

function generateColors(count: number): string[] {
  const palette = [
    '#2E86AB',
    '#A23B72',
    '#F18F01',
    '#C73E1D',
    '#3B1F2B',
    '#6D9DC5',
    '#C97B84',
    '#F9C74F',
    '#90BE6D',
    '#43AA8B',
  ];
  const colors: string[] = [];
  for (let i = 0; i < count; i++) {
    // palette.length is always 10, so this will always have a value
    colors.push(palette[i % palette.length] ?? '#2E86AB');
  }
  return colors;
}
