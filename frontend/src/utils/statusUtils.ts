import { ProfileStatus } from '../types/api';
import {
  Clock,
  Loader2,
  CheckCircle,
  XCircle,
  Activity,
  Brain
} from 'lucide-react';

export function getStatusIcon(status: ProfileStatus) {
  switch (status) {
    case ProfileStatus.PENDING:
      return Clock;
    case ProfileStatus.SCRAPING:
    case ProfileStatus.PROCESSING:
      return Loader2;
    case ProfileStatus.ANALYZING:
      return Brain;
    case ProfileStatus.COMPLETED:
      return CheckCircle;
    case ProfileStatus.FAILED:
      return XCircle;
    default:
      return Activity;
  }
}

export function getStatusColor(status: ProfileStatus): string {
  switch (status) {
    case ProfileStatus.PENDING:
      return 'status-pending';
    case ProfileStatus.SCRAPING:
    case ProfileStatus.PROCESSING:
    case ProfileStatus.ANALYZING:
      return 'status-processing';
    case ProfileStatus.COMPLETED:
      return 'status-completed';
    case ProfileStatus.FAILED:
      return 'status-failed';
    default:
      return 'status-pending';
  }
}
