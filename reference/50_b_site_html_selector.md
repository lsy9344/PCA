참고사항
'적용해야 할 쿠폰'에 의해 적용되는 1회 쿠폰 로직은 [A]~[D] 코드 참고
예)'적용해야 할 쿠폰'의 '무료 1시간쿠폰' = 2 일 경우 [A]~[D] 코드 2회 반복한다.

test('test', async ({ page }) => {
  await page.goto('https://a15878.parkingweb.kr/login');// 웹페이지 접속
  await page.getByRole('textbox', { name: 'ID' }).fill('215');// 아이디 입력
  await page.getByRole('textbox', { name: 'PASSWORD' }).fill('4318');// 비밀번호 입력
  await page.getByRole('button', { name: 'Submit' }).click();// 로그인 버튼 클릭
  await page.locator('div').filter({ hasText: /^안내$/ }).click();// 안내 메시지 팝업 확인 (로그인 성공 확인)
  await page.getByText('OK').click();// 확인 버튼 클릭
  await page.getByRole('heading', { name: '할인내역' }).click();// '할인내역'이름의 테이블 찾기
  //await page.getByRole('cell', { name: '할인값' }).click();// '할인내역'테이블에 속한 '할인값' 찾기
  await page.locator('#gridDtl > .objbox').click();// '할인내역'테이블에 속한 적용된 쿠폰이 있는 칸 찾기
  await page.getByRole('textbox', { name: '차량번호' }).fill('1355');// '차량번호' 입력
  await page.getByRole('button', { name: '검색' }).click();// '검색' 버튼 클릭
  await page.getByText('허1355').click();// 차량번호 검색 버튼 누른 후 존재유무 확인하기
  await page.getByRole('link', { name: '무료 1시간할인' }).click();// 무료 1시간할인 쿠폰 적용[A]
  await page.getByText('등록되었습니다').click();// 쿠폰 등록 '등록되었습니다' 팝업창 확인[B]
  await page.getByText('OK').click();// 확인 버튼 클릭[C]
  await page.getByRole('cell', { name: '무료 1시간할인', exact: true }).click();// '할인내역'테이블에 속한 적용된 쿠폰이 있는 칸에서 '무료 1시간할인' 쿠폰 적용 확인//[D]
  await page.getByRole('link', { name: '유료 30분할인 (판매 : 300 )' }).click();// 첫 번째 '유료 30분할인' 쿠폰 적용
  await page.getByText('등록되었습니다').click();// 쿠폰 등록 '등록되었습니다' 팝업창 확인
  await page.getByText('OK').click();// 확인 버튼 클릭
  await page.getByRole('cell', { name: '유료 30분할인' }).first().click();// '할인내역'테이블에 속한 적용된 쿠폰이 있는 칸에서 첫 번째 '유료 30분할인' 쿠폰 적용 확인
  //'유료 30분할인' 첫 번째 쿠폰이 적용되면 .first()에 배열 됨
  await page.getByRole('link', { name: '유료 30분할인 (판매 : 300 )' }).click();// 두 번째 '유료 30분할인' 쿠폰 적용
  await page.getByText('등록되었습니다').click();// 쿠폰 등록 '등록되었습니다' 팝업창 확인
  await page.getByText('OK').click();// 확인 버튼 클릭
  await page.getByRole('cell', { name: '유료 30분할인' }).first().click();// '할인내역'테이블에 속한 적용된 쿠폰이 있는 칸에서 두 번째 '유료 30분할인' 쿠폰 적용 확인
  //'유료 30분할인' 두 번째 쿠폰이 적용되면 .first(), .nth(1) 배열 됨
  await page.getByRole('link', { name: '유료 30분할인 (판매 : 300 )' }).click();// 세 번째 유료 30분할인 쿠폰 적용
  await page.getByText('등록되었습니다').click();// 쿠폰 등록 '등록되었습니다' 팝업창 확인
  await page.getByText('OK').click();// 확인 버튼 클릭
  await page.getByRole('cell', { name: '유료 30분할인' }).nth(2).click();// '할인내역'테이블에 속한 적용된 쿠폰이 있는 칸에서 세 번째 '유료 30분할인' 쿠폰 적용 확인
  //'유료 30분할인' 두 번째 쿠폰이 적용되면 .first(), .nth(1), .nth(2) 배열 됨
  await page.getByRole('button', { name: 'LOGOUT' }).click();// 로그아웃 버튼 클릭
});