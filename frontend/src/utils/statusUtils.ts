import { ProfileStatus, PostStatus } from '../types/api';
import {
  Clock,
  Loader2,
  CheckCircle,
  XCircle,
  Activity,
  Brain
} from 'lucide-react';

type Status = ProfileStatus | PostStatus;

export function getStatusIcon(status: Status) {
  switch (status) {
    case ProfileStatus.PENDING:
    case PostStatus.PENDING:
      return Clock;
    case ProfileStatus.SCRAPING:
    case ProfileStatus.PROCESSING:
    case PostStatus.SCRAPING:
    case PostStatus.PROCESSING:
      return Loader2;
    case ProfileStatus.ANALYZING:
    case PostStatus.ANALYZING:
      return Brain;
    case ProfileStatus.COMPLETED:
    case PostStatus.COMPLETED:
      return CheckCircle;
    case ProfileStatus.FAILED:
    case PostStatus.FAILED:
      return XCircle;
    default:
      return Activity;
  }
}

export function getStatusColor(status: Status): string {
  switch (status) {
    case ProfileStatus.PENDING:
    case PostStatus.PENDING:
      return 'status-pending';
    case ProfileStatus.SCRAPING:
    case ProfileStatus.PROCESSING:
    case ProfileStatus.ANALYZING:
    case PostStatus.SCRAPING:
    case PostStatus.PROCESSING:
    case PostStatus.ANALYZING:
      return 'status-processing';
    case ProfileStatus.COMPLETED:
    case PostStatus.COMPLETED:
      return 'status-completed';
    case ProfileStatus.FAILED:
    case PostStatus.FAILED:
      return 'status-failed';
    default:
      return 'status-pending';
  }
}
