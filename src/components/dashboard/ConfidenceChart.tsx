import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import type { StatsResponse } from '@/types';

interface ConfidenceChartProps {
  stats: StatsResponse | null;
}

const COLORS = {
  'high (>=0.85)': '#10b981',
  'medium (0.60-0.85)': '#f59e0b',
  'low (<0.60)': '#6b7280',
};

export function ConfidenceChart({ stats }: ConfidenceChartProps) {
  if (!stats?.confidence_distribution?.length) {
    return (
      <Card className="col-span-1">
        <CardHeader>
          <CardTitle className="text-base font-semibold">Match Confidence Distribution</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[250px]">
          <p className="text-muted-foreground text-sm">No data available</p>
        </CardContent>
      </Card>
    );
  }

  const data = stats.confidence_distribution.map((item) => ({
    name: item.confidence_band,
    value: item.count,
    fill: COLORS[item.confidence_band as keyof typeof COLORS] || '#8884d8',
  }));

  const total = data.reduce((sum, item) => sum + item.value, 0);

  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="text-base font-semibold">Match Confidence Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={4}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number) => [`${value.toLocaleString()} (${((value / total) * 100).toFixed(1)}%)`, 'Count']}
              contentStyle={{ fontSize: '12px', borderRadius: '8px' }}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ fontSize: '11px' }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="grid grid-cols-3 gap-2 mt-2 text-center">
          <div className="bg-emerald-50 rounded-lg p-2">
            <div className="text-lg font-bold text-emerald-600">
              {stats.match_status_distribution?.auto_merge?.toLocaleString() || '0'}
            </div>
            <div className="text-xs text-muted-foreground">Auto Merge</div>
          </div>
          <div className="bg-amber-50 rounded-lg p-2">
            <div className="text-lg font-bold text-amber-600">
              {stats.match_status_distribution?.review?.toLocaleString() || '0'}
            </div>
            <div className="text-xs text-muted-foreground">Review</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-2">
            <div className="text-lg font-bold text-gray-600">
              {stats.match_status_distribution?.distinct?.toLocaleString() || '0'}
            </div>
            <div className="text-xs text-muted-foreground">Distinct</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
