import React from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';

export default function Home() {
  return (
    <Layout
      title="Cifra Docs"
      description="Быстрый адаптивный SEO-оптимизированный фронтенд документации на Docusaurus"
    >
      <main className="heroWrap">
        <section className="container heroSection">
          <p className="kicker">SEO-ready • Mobile-first • Docusaurus</p>
          <h1>Полная документация Cifra на Docusaurus</h1>
          <p>
            Быстрый адаптивный frontend-портал документации: roadmap, CSV-схема,
            загрузка тестовых данных и строгая валидация перед WordPress импортом.
          </p>
          <div className="heroButtons">
            <Link className="button button--primary button--lg" to="/docs/intro">
              Открыть документацию
            </Link>
            <Link className="button button--secondary button--lg" to="/docs/csv-validator">
              CSV Validator
            </Link>
          </div>
        </section>
      </main>
    </Layout>
  );
}
