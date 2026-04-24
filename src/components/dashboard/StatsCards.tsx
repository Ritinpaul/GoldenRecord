import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Database, Users, GitMerge, AlertTriangle, CheckCircle } from 'lucide-react';
import type { HealthResponse } from '@/types';

interface StatsCardsProps {
  health: HealthResponse | null;
}

export function StatsCards({ health }: StatsCardsProps) {
  if (!health) return null;

  const cards = [
    {
      title: 'Raw CRM Primary',
      value: health.records?.raw_crm_primary?.toLocaleString() || '0',
      icon: Database,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      title: 'Raw CRM Secondary',
      value: health.records?.raw_crm_secondary?.toLocaleString() || '0',
      icon: Database,
      color: 'text-cyan-600',
      bg: 'bg-cyan-50',
    },
    {
      title: 'Marketing Contacts',
      value: health.records?.raw_marketing?.toLocaleString() || '0',
      icon: Database,
      color: 'text-violet-600',
      bg: 'bg-violet-50',
    },
    {
      title: 'Golden Records',
      value: health.records?.golden_records?.toLocaleString() || '0',
      icon: Users,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
    },
    {
      title: 'Match Results',
      value: health.records?.match_results?.toLocaleString() || '0',
      icon: GitMerge,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
    },
    {
      title: 'Status',
      value: health.status === 'healthy' ? 'Healthy' : 'Degraded',
      icon: health.status === 'healthy' ? CheckCircle : AlertTriangle,
      color: health.status === 'healthy' ? 'text-green-600' : 'text-red-600',
      bg: health.status === 'healthy' ? 'bg-green-50' : 'bg-red-50',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map((card) => (
        <Card key={card.title} className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {card.title}
            </CardTitle>
            <div className={`${card.bg} p-2 rounded-lg`}>
              <card.icon className={`h-4 w-4 ${card.color}`} />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
