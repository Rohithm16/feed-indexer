import type { FC } from 'react';
import { useTimeOfDay } from '../hooks/useTimeOfDay';

interface Props {
  className?: string;
  as?: 'span' | 'h1' | 'h2';
}

const BrandTitle: FC<Props> = ({ className = '', as: Tag = 'span' }) => {
  const timePeriod = useTimeOfDay();

  return (
    <Tag className={`brand-title ${className}`.trim()} data-time={timePeriod}>
      Feed Indexer
    </Tag>
  );
};

export default BrandTitle;
