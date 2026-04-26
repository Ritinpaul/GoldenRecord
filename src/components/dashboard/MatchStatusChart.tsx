import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { StatsResponse } from '@/types';

interface MatchStatusChartProps {
  stats: StatsResponse | null;
}

export function MatchStatusChart({ stats }: MatchStatusChartProps) {
  const data = stats?.confidence_distribution || [];

  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="text-base font-semibold">Confidence Score Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis
                dataKey="confidence_band"
                type="category"
                tick={{ fontSize: 11 }}
                width={140}
              />
              <Tooltip
                formatter={(value: number) => [value.toLocaleString(), 'Records']}
                contentStyle={{ fontSize: '12px', borderRadius: '8px' }}
              />
              <Bar
                dataKey="count"
                fill="#3b82f6"
                radius={[0, 4, 4, 0]}
                name="Records"
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[250px]">
            <p className="text-muted-foreground text-sm">No data available</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
