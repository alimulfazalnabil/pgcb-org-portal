'use client';

import { useEffect, useState } from 'react';
import { api, DocumentItem } from '../../lib/api';
import { LoadingState } from '../../components/ui/LoadingState';
import { EmptyState } from '../../components/ui/EmptyState';
import { Pagination } from '../../components/ui/Pagination';
import { Search, Download } from 'lucide-react';
import { useLanguage } from '../../lib/i18n';

const CATEGORIES = [
  { labelBn: 'সকল ডকুমেন্টস', labelEn: 'All Documents', value: '' },
  { labelBn: 'ফরম (Forms)', labelEn: 'Forms', value: 'FORM' },
  { labelBn: 'নীতিমালা (Policies)', labelEn: 'Policies', value: 'POLICY' },
  { labelBn: 'বার্ষিক প্রতিবেদন (Reports)', labelEn: 'Annual Reports', value: 'REPORT' },
  { labelBn: 'ম্যানুয়াল ও নির্দেশিকা', labelEn: 'Manuals & Guidelines', value: 'MANUAL' },
  { labelBn: 'সার্কুলার', labelEn: 'Circulars', value: 'CIRCULAR' },
  { labelBn: 'অন্যান্য', labelEn: 'Other', value: 'OTHER' },
];

function formatBytes(bytes?: number): string {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentsPage() {
  const { language, t, pick, formatNumber } = useLanguage();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('');
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    setLoading(true);
    api.getDocuments({
      category: category || undefined,
      page,
      limit: 15,
    })
      .then((data) => {
        setDocuments(data);
      })
      .catch((err) => {
        console.error('Failed to load documents', err);
        setDocuments([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [category, page]);

  const filteredDocs = documents.filter((d) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      d.title_bn.toLowerCase().includes(q) ||
      (d.title_en && d.title_en.toLowerCase().includes(q)) ||
      (d.description_bn && d.description_bn.toLowerCase().includes(q)) ||
      (d.description_en && d.description_en.toLowerCase().includes(q))
    );
  });

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 min-h-screen">
      <div className="border-b border-slate-200 pb-6 mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-2">
          {t('প্রাতিষ্ঠানিক ডকুমেন্টস ও ফরম সংগ্রহশালা', 'Institutional Documents & Forms Repository')}
        </h1>
        <p className="text-slate-600 text-sm md:text-base">
          {t(
            'পিজিসিবি প্রকৌশলী সমিতির সদস্য ফরম, কল্যাণ নীতিমালা, বার্ষিক নিরীক্ষা রিপোর্ট ও অফিশিয়াল প্রকাশনাসমূহ ডাউনলোড করুন।',
            'Download membership forms, welfare policies, annual audit reports, and official publications of the PGCB Engineers Association.'
          )}
        </p>
      </div>

      {/* Filter and Search */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center mb-8">
        <div className="flex flex-wrap gap-2 w-full md:w-auto">
          {CATEGORIES.map((c) => (
            <button
              key={c.value}
              onClick={() => {
                setCategory(c.value);
                setPage(1);
              }}
              className={`px-3.5 py-1.5 rounded-lg text-xs md:text-sm font-medium transition-all ${
                category === c.value
                  ? 'bg-emerald-700 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {t(c.labelBn, c.labelEn)}
            </button>
          ))}
        </div>

        <div className="relative w-full md:w-72">
          <Search size={16} className="absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder={t('ডকুমেন্ট খুঁজুন...', 'Search documents...')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
          />
        </div>
      </div>

      {/* List */}
      {loading ? (
        <LoadingState message={t('ডকুমেন্ট তালিকা লোড হচ্ছে...', 'Loading documents...')} />
      ) : filteredDocs.length === 0 ? (
        <EmptyState
          icon="📂"
          title={t('কোনো দলিল পাওয়া যায়নি', 'No documents found')}
          description={t('বর্তমানে এই ক্যাটাগরিতে কোনো নথি বা ফরম আপলোড করা হয়নি।', 'No documents or forms have been uploaded in this category yet.')}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-xs">
                  <th className="py-3 px-4">{t('ডকুমেন্টের নাম ও বিবরণ', 'Document Name & Description')}</th>
                  <th className="py-3 px-4">{t('ক্যাটাগরি', 'Category')}</th>
                  <th className="py-3 px-4">{t('ভার্সন', 'Version')}</th>
                  <th className="py-3 px-4">{t('ফাইল সাইজ', 'File Size')}</th>
                  <th className="py-3 px-4">{t('ডাউনলোড', 'Downloads')}</th>
                  <th className="py-3 px-4 text-right">{t('অ্যাকশন', 'Action')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-4 px-4">
                      <div className="font-semibold text-slate-900">{pick(doc, 'title', doc.title_bn)}</div>
                      {language === 'bn' && doc.title_en && <div className="text-xs text-slate-500 italic">{doc.title_en}</div>}
                      {(doc.description_bn || doc.description_en) && (
                        <div className="text-xs text-slate-600 mt-1 line-clamp-1">
                          {pick(doc, 'description', doc.description_bn || '')}
                        </div>
                      )}
                    </td>
                    <td className="py-4 px-4">
                      <span className="bg-emerald-50 text-emerald-700 text-xs font-medium px-2 py-0.5 rounded">
                        {doc.category}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-xs font-mono text-slate-500">v{doc.version}</td>
                    <td className="py-4 px-4 text-xs text-slate-500">{formatBytes(doc.file_size)}</td>
                    <td className="py-4 px-4 text-xs text-slate-500">
                      {language === 'en' ? `${formatNumber(doc.download_count)} times` : `${formatNumber(doc.download_count)} বার`}
                    </td>
                    <td className="py-4 px-4 text-right">
                      <a
                        href={api.getDocumentDownloadUrl(doc.id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-md text-xs font-medium transition-colors shadow-sm"
                      >
                        <Download size={13} /> {t('ডাউনলোড', 'Download')}
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination */}
      <Pagination
        currentPage={page}
        totalPages={Math.max(1, Math.ceil(filteredDocs.length / 15))}
        onPageChange={(newPage) => setPage(newPage)}
      />
    </div>
  );
}
