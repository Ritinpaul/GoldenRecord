import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { StatsResponse } from '@/types';

interface QualityTrendsProps {
  stats: StatsResponse | null;
}

export function QualityTrends({ stats }: QualityTrendsProps) {
  const trends = stats?.quality_trends || [];

  // Group by source_system
  const bySource: Record<string, Array<{ date: string; completeness: number; duplicateRate: number }>> = {};

  trends.forEach((item) => {
    const key = item.source_system || 'unknown';
    if (!bySource[key]) bySource[key] = [];
    bySource[key].push({
      date: item.snapshot_date,
      completeness: item.completeness_pct || 0,
      duplicateRate: item.duplicate_rate || 0,
    });
  });

  // Use all data as single series if no grouping
  const chartData = trends.length > 0
    ? trends.map((item) => ({
        date: item.snapshot_date,
        completeness: item.completeness_pct || 0,
        duplicateRate: item.duplicate_rate || 0,
      }))
    : [];

  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle className="text-base font-semibold">Data Quality Trends</CardTitle>
      </CardHeader>
      <CardContent>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11 }}
                tickFormatter={(value) => {
                  const d = new Date(value);
                  return `${d.getMonth() + 1}/${d.getDate()}`;
                }}
              />
              <YAxis tick={{ fontSize: 11 }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{ fontSize: '12px', borderRadius: '8px' }}
                formatter={(value: number, name: string) => [`${value.toFixed(1)}%`, name === 'completeness' ? 'Completeness' : 'Duplicate Rate']}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Line
                type="monotone"
                dataKey="completeness"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
                name="Completeness %"
              />
              <Line
                type="monotone"
                dataKey="duplicateRate"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
                name="Duplicate Rate %"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[250px]">
            <p className="text-muted-foreground text-sm">No quality data yet - run pipeline first</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
